#!/usr/bin/env python3
"""
dlp_windows_service.py
Windows Service for DLP Upload Monitoring
Automatically starts on system boot and monitors for file uploads.
"""

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import time
import logging
import threading
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from network_monitor_agent import NetworkUploadMonitor
from upload_monitor_agent import UploadMonitorAgent
from http_upload_blocker import HTTPUploadBlocker

class DLPMonitorService(win32serviceutil.ServiceFramework):
    """Windows Service for DLP Upload Monitoring"""

    _svc_name_ = "DLPMonitorService"
    _svc_display_name_ = "DLP Upload Monitor Service"
    _svc_description_ = "Monitors file uploads and requires admin approval"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = False

        # Setup logging
        log_dir = Path("C:/ProgramData/DLPMonitor/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "dlp_service.log"),
                logging.StreamHandler()
            ]
        )

    def SvcStop(self):
        """Stop the service"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
        logging.info("DLP Service stop requested")

    def SvcDoRun(self):
        """Run the service"""
        self.running = True
        logging.info("DLP Service starting...")

        try:
            self._run_monitoring()
        except Exception as e:
            logging.error(f"Service error: {e}")
            self.running = False

    def _run_monitoring(self):
        """Run the monitoring components"""
        logging.info("Starting DLP monitoring components...")

        # Start network monitor
        network_monitor = NetworkUploadMonitor()
        network_monitor.start_monitoring()

        # Start file system monitor
        file_monitor = UploadMonitorAgent()
        file_monitor.start_monitoring()

        # Start HTTP upload blocker
        http_blocker = HTTPUploadBlocker()
        http_blocker.start_blocking()

        logging.info("All DLP monitoring components started")

        # Keep service running
        while self.running:
            # Check if stop event is signaled
            if win32event.WaitForSingleObject(self.stop_event, 1000) == win32event.WAIT_OBJECT_0:
                break

        # Cleanup
        logging.info("Stopping DLP monitoring components...")
        network_monitor.stop_monitoring()
        file_monitor.stop_monitoring()
        http_blocker.stop_blocking()
        logging.info("DLP Service stopped")

def install_service():
    """Install the Windows service"""
    try:
        win32serviceutil.InstallService(
            DLPMonitorService._svc_name_,
            DLPMonitorService._svc_display_name_,
            DLPMonitorService._svc_description_
        )
        print("✅ DLP Service installed successfully!")
        print("To start the service: net start DLPMonitorService")
        print("To stop the service: net stop DLPMonitorService")
    except Exception as e:
        print(f"❌ Failed to install service: {e}")

def uninstall_service():
    """Uninstall the Windows service"""
    try:
        win32serviceutil.RemoveService(DLPMonitorService._svc_name_)
        print("✅ DLP Service uninstalled successfully!")
    except Exception as e:
        print(f"❌ Failed to uninstall service: {e}")

def main():
    """Main function"""
    if len(sys.argv) == 1:
        # Run as service
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(DLPMonitorService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Handle command line arguments
        if sys.argv[1] == 'install':
            install_service()
        elif sys.argv[1] == 'uninstall':
            uninstall_service()
        else:
            win32serviceutil.HandleCommandLine(DLPMonitorService)

if __name__ == '__main__':
    main()
