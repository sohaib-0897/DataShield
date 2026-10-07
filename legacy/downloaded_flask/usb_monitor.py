import time
import win32com.client

from database import initialize_database, log_activity


def get_usb_drives():

    drives = set()

    wmi = win32com.client.GetObject(
        "winmgmts:"
    )

    for drive in wmi.InstancesOf("Win32_DiskDrive"):

        if "USB" in str(drive.InterfaceType):

            for partition in drive.Associators_(
                "Win32_DiskDriveToDiskPartition"
            ):

                for logical_disk in partition.Associators_(
                    "Win32_LogicalDiskToPartition"
                ):

                    drives.add(
                        logical_disk.DeviceID
                    )

    return drives


def main():

    initialize_database()

    print("===================================")
    print("        AI-DLP USB MONITOR")
    print("===================================")
    print("Monitoring USB devices...")
    print("Press CTRL+C to stop.")
    print()

    previous_drives = get_usb_drives()

    print(
        f"Currently connected USB drives: "
        f"{previous_drives}"
    )

    try:

        while True:

            current_drives = get_usb_drives()

            # -----------------------------
            # USB INSERTED
            # -----------------------------

            inserted = current_drives - previous_drives

            for drive in inserted:

                print()
                print("===================================")
                print("[USB INSERTED]")
                print("===================================")
                print(f"Drive: {drive}")
                print("===================================")

                log_activity(
                    "USB_INSERTED",
                    drive,
                    "NORMAL",
                    "SYSTEM"
                )

            # -----------------------------
            # USB REMOVED
            # -----------------------------

            removed = previous_drives - current_drives

            for drive in removed:

                print()
                print("===================================")
                print("[USB REMOVED]")
                print("===================================")
                print(f"Drive: {drive}")
                print("===================================")

                log_activity(
                    "USB_REMOVED",
                    drive,
                    "NORMAL",
                    "SYSTEM"
                )

            previous_drives = current_drives

            time.sleep(2)

    except KeyboardInterrupt:

        print()
        print("Stopping USB monitor...")


if __name__ == "__main__":
    main()