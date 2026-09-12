#!/usr/bin/env python3

import os
import sys
import time
import logging
import threading
import requests
import platform
import re
from datetime import datetime
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
    GUI_AVAILABLE = True
except:
    GUI_AVAILABLE = False


DEFAULT_ADMIN_URL = "http://127.0.0.1:5000"
DEFAULT_API_KEY = os.environ["DATASHIELD_API_KEY"]

CNIC_PATTERN = re.compile(r"\b\d{5}-\d{7}-\d\b")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)


class UploadMonitorAgent:

    def __init__(self):

        self.client_name = os.getenv("COMPUTERNAME") or platform.node()
        self.observer = None
        self.monitoring = False

        home = Path.home()

        self.config = {
            "admin_url": DEFAULT_ADMIN_URL,
            "api_key": DEFAULT_API_KEY,
            "monitor_folders": [
                str(home / "Desktop"),
                str(home / "Downloads"),
                str(home / "Documents"),
                str(home / "Pictures")
            ],
            "file_extensions": [
                ".txt", ".pdf", ".docx", ".doc",
                ".xls", ".xlsx", ".csv",
                ".json", ".xml",
                ".ppt", ".pptx",
                ".jpg", ".jpeg", ".png",
                ".zip", ".rar", ".7z"
            ],
            "max_file_size_mb": 10,
            "preview_chars": 800
        }


    def scan_file(self, file_path):

        result = {
            "sensitive": False,
            "sensitive_matches": [],
            "preview": None,
            "file_size": None,
            "modified_time": None
        }

        try:

            p = Path(file_path)

            if not p.exists():
                return result

            result["file_size"] = p.stat().st_size
            result["modified_time"] = datetime.fromtimestamp(
                p.stat().st_mtime).isoformat()

            max_bytes = self.config["max_file_size_mb"] * 1024 * 1024

            if p.stat().st_size > max_bytes:
                return result

            with open(file_path, "rb") as f:
                raw = f.read(4096)

            text = raw.decode("utf-8", errors="ignore")

            matches = CNIC_PATTERN.findall(text)

            if matches:
                result["sensitive"] = True
                result["sensitive_matches"] = list(set(matches))

            result["preview"] = text[:self.config["preview_chars"]]

        except Exception as e:
            logging.debug(f"scan error {e}")

        return result


    def send_alert(self, activity, filename, file_path, new_path=None):

        endpoint = self.config["admin_url"] + "/file_activity_alert"

        scan = self.scan_file(file_path)

        payload = {
            "client": self.client_name,
            "activity": activity,
            "filename": filename,
            "file_path": file_path,
            "new_path": new_path,
            "timestamp": datetime.now().isoformat(),
            **scan
        }

        try:

            r = requests.post(
                endpoint,
                json=payload,
                headers={"X-API-KEY": self.config["api_key"]},
                timeout=5
            )

            if r.status_code == 200:
                logging.info(f"Alert sent: {activity} {filename}")

        except Exception as e:
            logging.error(f"Alert failed {e}")


class FileHandler(FileSystemEventHandler):

    def __init__(self, agent):
        self.agent = agent

    def on_created(self, event):

        if event.is_directory:
            return

        path = event.src_path
        name = os.path.basename(path)

        logging.info(f"Created {path}")
        self.agent.send_alert("created", name, path)

    def on_modified(self, event):

        if event.is_directory:
            return

        path = event.src_path
        name = os.path.basename(path)

        logging.info(f"Modified {path}")
        self.agent.send_alert("modified", name, path)

    def on_deleted(self, event):

        if event.is_directory:
            return

        path = event.src_path
        name = os.path.basename(path)

        logging.info(f"Deleted {path}")
        self.agent.send_alert("deleted", name, path)

    def on_moved(self, event):

        if event.is_directory:
            return

        old = event.src_path
        new = event.dest_path

        name = os.path.basename(new)

        logging.info(f"Moved {old} -> {new}")
        self.agent.send_alert("moved", name, old, new)


def start_monitoring(agent):

    if agent.monitoring:
        logging.info("Monitoring already running")
        return

    observer = Observer()
    handler = FileHandler(agent)

    for folder in agent.config["monitor_folders"]:

        if os.path.exists(folder):

            observer.schedule(handler, folder, recursive=True)
            logging.info(f"Monitoring {folder}")

    observer.start()

    agent.observer = observer
    agent.monitoring = True

    logging.info("Monitoring started")

    try:
        while agent.monitoring:
            time.sleep(1)

    finally:

        observer.stop()
        observer.join()

        agent.monitoring = False
        logging.info("Monitoring stopped")


def main():

    agent = UploadMonitorAgent()

    if not GUI_AVAILABLE:

        start_monitoring(agent)
        return

    root = tk.Tk()
    root.title("DataShield Upload Monitor")
    root.geometry("500x150")

    frame = ttk.Frame(root, padding=10)
    frame.pack(fill="both", expand=True)

    ttk.Label(
        frame,
        text="DataShield DLP Monitor",
        font=("Arial", 14, "bold")
    ).pack(pady=10)

    def start_clicked():

        if agent.monitoring:
            messagebox.showinfo("Running", "Monitoring already running")
            return

        btn_start.config(state="disabled")

        t = threading.Thread(
            target=start_monitoring,
            args=(agent,),
            daemon=True
        )

        t.start()

        messagebox.showinfo(
            "Started",
            "Monitoring started successfully"
        )

    def exit_app():

        if agent.observer:
            agent.monitoring = False
            agent.observer.stop()

        root.destroy()

    btn_start = ttk.Button(frame, text="Start Monitoring", command=start_clicked)
    btn_start.pack(pady=5)

    btn_exit = ttk.Button(frame, text="Exit", command=exit_app)
    btn_exit.pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    main()
