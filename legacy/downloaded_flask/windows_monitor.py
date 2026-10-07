import os
import time
import xml.etree.ElementTree as ET

import win32evtlog

from database import log_activity, initialize_database
from sensitivity import get_sensitivity


# ============================================================
# CONFIGURATION
# ============================================================

WATCH_DIRECTORY = os.path.normcase(
    os.path.abspath(
        r"C:\Users\Crown Tech\Desktop\AI-DLP-Agent\sensitive_files"
    )
)


# Monitor both:
# 4663 = access attempt (READ / WRITE / DELETE access)
# 4660 = object was deleted
QUERY = """
<QueryList>
    <Query Id="0">
        <Select Path="Security">
            *[System[(EventID=4663 or EventID=4660)]]
        </Select>
    </Query>
</QueryList>
"""


# Windows access codes
ACCESS_READ = {
    "%%4416",
    "%%4423"
}


ACCESS_WRITE = {
    "%%4417",
    "%%4418",
    "%%4419",
    "%%4420"
}


# Delete access
ACCESS_DELETE = {
    "%%1537"
}


# Applications that represent actual user activity.
USER_APPLICATIONS = {
    "notepad.exe",
    "winword.exe",
    "excel.exe",
    "powerpnt.exe",
    "acrord32.exe",
    "code.exe",
}


# Prevent multiple low-level Windows events
# from becoming duplicate activities.
activity_cache = {}

AGGREGATION_WINDOW = 3


# ============================================================
# DELETE CORRELATION CACHE
# ============================================================

# Event 4660 normally does NOT contain ObjectName.
#
# Event 4663 gives us:
#     HandleId -> ObjectName
#
# Event 4660 later tells us:
#     HandleId -> Object was deleted
#
# Therefore we temporarily remember the 4663 information.

handle_cache = {}


# ============================================================
# PATH NORMALIZATION
# ============================================================

def normalize_path(path):

    if not path:
        return None

    return os.path.normcase(
        os.path.abspath(path)
    )


# ============================================================
# EVENT XML PARSER
# ============================================================

def get_event_data(xml):

    root = ET.fromstring(xml)

    namespace = {
        "e": "http://schemas.microsoft.com/win/2004/08/events/event"
    }

    # Get Event ID
    event_id_element = root.find(
        ".//e:System/e:EventID",
        namespace
    )

    event_id = (
        event_id_element.text
        if event_id_element is not None
        else None
    )

    # Get EventData fields
    data = {}

    for item in root.findall(
        ".//e:EventData/e:Data",
        namespace
    ):

        name = item.attrib.get("Name")
        value = item.text

        if name:
            data[name] = value

    return event_id, data


# ============================================================
# ACCESS CLASSIFICATION
# ============================================================

def classify_access(access_list):

    if not access_list:
        return None

    codes = set(
        access_list.split()
    )

    if codes & ACCESS_DELETE:
        return "DELETE"

    if codes & ACCESS_WRITE:
        return "WRITE"

    if codes & ACCESS_READ:
        return "READ"

    return None


# ============================================================
# PROCESS NAME
# ============================================================

def get_process_name(process_path):

    if not process_path:
        return ""

    return os.path.basename(
        process_path
    ).lower()


# ============================================================
# CHECK MONITORED PATH
# ============================================================

def is_monitored_file(file_path):

    if not file_path:
        return False

    file_path = normalize_path(
        file_path
    )

    if file_path == WATCH_DIRECTORY:
        return False

    return file_path.startswith(
        WATCH_DIRECTORY + os.sep
    )


# ============================================================
# USER ACTIVITY LOGGING
# ============================================================

def print_activity(
    username,
    file_path,
    sensitivity,
    action,
    process_name
):

    print()
    print("===================================")
    print("[USER ACTIVITY DETECTED]")
    print("===================================")
    print(f"User:        {username}")
    print(f"File:        {file_path}")
    print(f"Sensitivity: {sensitivity}")
    print(f"Action:      {action}")
    print(f"Application: {process_name}")
    print("===================================")


# ============================================================
# EVENT PROCESSING
# ============================================================

def process_event(event):

    try:

        # ----------------------------------------------------
        # Render Windows event as XML
        # ----------------------------------------------------

        xml = win32evtlog.EvtRender(
            event,
            win32evtlog.EvtRenderEventXml
        )

        event_id, data = get_event_data(
            xml
        )

        # ----------------------------------------------------
        # Common event information
        # ----------------------------------------------------

        object_type = data.get(
            "ObjectType"
        )

        object_name = data.get(
            "ObjectName"
        )

        access_list = data.get(
            "AccessList"
        )

        username = data.get(
            "SubjectUserName"
        )

        process_path = data.get(
            "ProcessName"
        )

        process_name = get_process_name(
            process_path
        )

        handle_id = data.get(
            "HandleId"
        )


        # ====================================================
        # EVENT 4663
        # ====================================================

        if event_id == "4663":

            # Only monitor files
            if object_type != "File":
                return

            if not object_name:
                return

            file_path = normalize_path(
                object_name
            )

            # Only our monitored directory
            if not is_monitored_file(
                file_path
            ):
                return

            # Determine sensitivity
            sensitivity = get_sensitivity(
                file_path
            )

            # Ignore normal files
            if sensitivity == "NORMAL":
                return

            # ------------------------------------------------
            # Save handle information for possible deletion
            # ------------------------------------------------

            if handle_id:

                handle_cache[
                    handle_id
                ] = {
                    "file_path": file_path,
                    "username": username,
                    "process_name": process_name,
                    "sensitivity": sensitivity,
                    "timestamp": time.time()
                }


            # ------------------------------------------------
            # Determine action
            # ------------------------------------------------

            action = classify_access(
                access_list
            )

            if not action:
                return


            # ------------------------------------------------
            # DELETE ACCESS
            # ------------------------------------------------

            if action == "DELETE":

                # Do not immediately log deletion.
                #
                # Event 4660 confirms that the object
                # was actually deleted.

                return


            # ------------------------------------------------
            # User application filter
            # ------------------------------------------------

            if process_name not in USER_APPLICATIONS:
                return


            # ------------------------------------------------
            # Aggregation
            # ------------------------------------------------

            key = (
                file_path,
                username,
                process_name,
                action
            )

            now = time.time()

            last_seen = activity_cache.get(
                key
            )

            if last_seen is not None:

                if (
                    now - last_seen
                    <= AGGREGATION_WINDOW
                ):

                    activity_cache[
                        key
                    ] = now

                    return


            activity_cache[
                key
            ] = now


            # ------------------------------------------------
            # Log meaningful activity
            # ------------------------------------------------

            print_activity(
                username,
                file_path,
                sensitivity,
                action,
                process_name
            )

            log_activity(
                f"FILE_{action}",
                file_path,
                sensitivity,
                process_name
            )


        # ====================================================
        # EVENT 4660
        # ====================================================

        elif event_id == "4660":

            # 4660 often does NOT contain ObjectName.
            #
            # Therefore use HandleId to find the file
            # information saved from the earlier 4663 event.

            if not handle_id:
                return

            cached = handle_cache.get(
                handle_id
            )

            if not cached:
                return


            # ------------------------------------------------
            # Check cache expiration
            # ------------------------------------------------

            if (
                time.time()
                - cached["timestamp"]
                > 10
            ):

                handle_cache.pop(
                    handle_id,
                    None
                )

                return


            file_path = cached[
                "file_path"
            ]

            username = cached[
                "username"
            ]

            process_name = cached[
                "process_name"
            ]

            sensitivity = cached[
                "sensitivity"
            ]


            # ------------------------------------------------
            # Only monitored files
            # ------------------------------------------------

            if not is_monitored_file(
                file_path
            ):
                return


            if sensitivity == "NORMAL":
                return


            # ------------------------------------------------
            # Log confirmed deletion
            # ------------------------------------------------

            print_activity(
                username,
                file_path,
                sensitivity,
                "DELETE",
                process_name
            )

            log_activity(
                "FILE_DELETE",
                file_path,
                sensitivity,
                process_name
            )


            # Remove handle from cache
            handle_cache.pop(
                handle_id,
                None
            )


    except Exception as e:

        print(
            f"[ERROR PROCESSING EVENT] {e}"
        )


# ============================================================
# EVENT CALLBACK
# ============================================================

def callback(
    action,
    context,
    event
):

    if (
        action
        == win32evtlog.EvtSubscribeActionDeliver
    ):

        process_event(
            event
        )

    elif (
        action
        == win32evtlog.EvtSubscribeActionError
    ):

        print(
            "[EVENT LOG ERROR]"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    initialize_database()

    print("===================================")
    print("      AI-DLP FILE MONITOR")
    print("===================================")

    print(
        f"Monitoring: {WATCH_DIRECTORY}"
    )

    print(
        "Event source: Windows Security"
    )

    print(
        "Event IDs: 4663, 4660"
    )

    print(
        "Mode: REAL-TIME"
    )

    print()

    print(
        "Status: ACTIVE"
    )

    print(
        "Sensitive files only"
    )

    print(
        "User applications only"
    )

    print(
        "Activity aggregation: 3 seconds"
    )

    print()

    print(
        "Press CTRL+C to stop."
    )

    print()


    # --------------------------------------------------------
    # Subscribe to Windows Security events
    # --------------------------------------------------------

    subscription = win32evtlog.EvtSubscribe(

        "Security",

        win32evtlog.EvtSubscribeToFutureEvents,

        Query=QUERY,

        Callback=callback
    )


    try:

        while True:

            time.sleep(1)


    except KeyboardInterrupt:

        print()

        print(
            "Stopping monitor..."
        )


    finally:

        subscription.Close()


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":

    main()