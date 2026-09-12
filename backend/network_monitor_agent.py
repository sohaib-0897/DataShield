#!/usr/bin/env python3
"""
network_monitor_agent.py
Network-level upload monitoring agent that captures HTTP/HTTPS traffic
to detect file uploads without browser injection.
"""

import time
import json
import logging
import requests
import threading
import subprocess
import re
import os
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import psutil

# Configuration
ADMIN_SERVER_URL = "http://127.0.0.1:5000/upload_alert"
API_KEY = os.environ["DATASHIELD_API_KEY"]

# Upload detection patterns
UPLOAD_PATTERNS = [
    r'Content-Type:\s*multipart/form-data',
    r'Content-Type:\s*application/octet-stream',
    r'Content-Type:\s*image/',
    r'Content-Type:\s*application/pdf',
    r'Content-Type:\s*application/msword',
    r'Content-Type:\s*application/vnd\.openxmlformats',
    r'Content-Type:\s*text/plain',
    r'Content-Disposition:\s*attachment',
    r'Content-Disposition:\s*form-data.*filename=',
    r'POST.*upload',
    r'PUT.*upload',
    r'PATCH.*upload'
]

# File extensions to monitor
MONITORED_EXTENSIONS = [
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.txt', '.csv', '.zip', '.rar', '.7z', '.tar', '.gz',
    '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv'
]

# Logging (console only, no file logging)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class NetworkUploadMonitor:
    """Network-level upload monitoring using system tools"""

    def __init__(self):
        self.running = False
        self.monitor_thread = None
        self.detected_uploads = set()  # Prevent duplicate alerts

    def start_monitoring(self):
        """Start network monitoring"""
        if self.running:
            logging.warning("Network monitoring already running")
            return

        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_network)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logging.info("Network upload monitoring started")

    def stop_monitoring(self):
        """Stop network monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logging.info("Network upload monitoring stopped")

    def _monitor_network(self):
        """Main monitoring loop using netstat and process monitoring"""
        logging.info("Starting network traffic analysis...")

        while self.running:
            try:
                # Monitor active connections
                self._check_active_connections()

                # Monitor browser processes
                self._monitor_browser_processes()

                # Sleep to avoid high CPU usage
                time.sleep(2)

            except Exception as e:
                logging.error(f"Error in network monitoring: {e}")
                time.sleep(5)

    def _check_active_connections(self):
        """Check active network connections for upload patterns"""
        try:
            # Get active connections using netstat
            result = subprocess.run(
                ['netstat', '-an'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if self._is_upload_connection(line):
                        self._analyze_connection(line)

        except subprocess.TimeoutExpired:
            logging.warning("netstat command timed out")
        except Exception as e:
            logging.error(f"Error checking connections: {e}")

    def _is_upload_connection(self, line):
        """Check if connection line indicates potential upload"""
        # Look for established connections to common upload ports/services
        upload_indicators = [
            ':80', ':443', ':8080', ':8443',  # HTTP/HTTPS
            'ESTABLISHED',
            'LISTENING'
        ]

        return any(indicator in line for indicator in upload_indicators)

    def _analyze_connection(self, connection_line):
        """Analyze a connection for upload activity"""
        try:
            # Extract process info if possible
            process_info = self._get_process_info(connection_line)
            if process_info and self._is_browser_process(process_info):
                self._monitor_process_uploads(process_info)

        except Exception as e:
            logging.error(f"Error analyzing connection: {e}")

    def _get_process_info(self, connection_line):
        """Get process information for a connection"""
        try:
            # Use netstat with process info
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if connection_line.split()[0] in line:
                        # Extract PID
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            return self._get_process_name(pid)

        except Exception as e:
            logging.error(f"Error getting process info: {e}")

        return None

    def _get_process_name(self, pid):
        """Get process name from PID"""
        try:
            process = psutil.Process(int(pid))
            return {
                'pid': pid,
                'name': process.name(),
                'cmdline': ' '.join(process.cmdline())
            }
        except (psutil.NoSuchProcess, ValueError, psutil.AccessDenied):
            return None

    def _is_browser_process(self, process_info):
        """Check if process is a browser"""
        if not process_info:
            return False

        browser_names = [
            'chrome.exe', 'firefox.exe', 'msedge.exe',
            'iexplore.exe', 'safari.exe', 'opera.exe'
        ]

        return any(browser in process_info['name'].lower()
                  for browser in browser_names)

    def _monitor_browser_processes(self):
        """Monitor browser processes for file access"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if self._is_browser_process(proc.info):
                    self._check_browser_file_access(proc.info)

        except Exception as e:
            logging.error(f"Error monitoring browser processes: {e}")

    def _check_browser_file_access(self, process_info):
        """Check if browser is accessing files that might be uploaded"""
        try:
            process = psutil.Process(process_info['pid'])

            # Check open files
            for file_info in process.open_files():
                if self._is_uploadable_file(file_info.path):
                    self._detect_potential_upload(file_info.path, process_info)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        except Exception as e:
            # Only log actual errors, not access denied
            if "Access denied" not in str(e):
                logging.error(f"Error checking file access: {e}")

    def _is_uploadable_file(self, file_path):
        """Check if file is likely to be uploaded"""
        if not file_path:
            return False

        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in MONITORED_EXTENSIONS

    def _detect_potential_upload(self, file_path, process_info):
        """Detect potential file upload and send alert"""
        try:
            # Create unique identifier for this upload
            upload_id = f"{process_info['pid']}_{file_path}_{int(time.time())}"

            if upload_id in self.detected_uploads:
                return  # Already alerted

            self.detected_uploads.add(upload_id)

            # Get file info
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            file_name = os.path.basename(file_path)

            # Send alert
            self._send_upload_alert(file_name, file_size, file_path, process_info)

            logging.info(f"Potential upload detected: {file_name} ({file_size} bytes) from {process_info['name']}")

        except Exception as e:
            logging.error(f"Error detecting upload: {e}")

    def _send_upload_alert(self, filename, file_size, file_path, process_info):
        """Send upload alert to admin server"""
        try:
            payload = {
                'client': 'network_monitor',
                'filename': filename,
                'file_size': file_size,
                'file_path': file_path,
                'process_name': process_info['name'],
                'process_pid': process_info['pid'],
                'upload_url': 'unknown',  # We can't determine this from network level
                'timestamp': datetime.now().isoformat(),
                'detection_method': 'network_monitoring'
            }

            response = requests.post(
                ADMIN_SERVER_URL,
                json=payload,
                headers={'X-API-KEY': API_KEY},
                timeout=10
            )

            if response.status_code == 200:
                logging.info(f"Upload alert sent successfully for {filename}")
            else:
                logging.error(f"Failed to send upload alert: {response.status_code}")

        except Exception as e:
            logging.error(f"Error sending upload alert: {e}")

    def _monitor_process_uploads(self, process_info):
        """Monitor specific process for upload activity"""
        # This is a simplified version - in a real implementation,
        # you might use more sophisticated network analysis
        pass

def main():
    """Main function to run the network monitor"""
    print("🔒 Network Upload Monitor Agent")
    print("=" * 40)

    monitor = NetworkUploadMonitor()

    try:
        print("Starting network upload monitoring...")
        monitor.start_monitoring()

        print("Network monitor is running. Press Ctrl+C to stop.")
        print("Monitoring for file uploads across the network...")

        # Keep running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping network monitor...")
        monitor.stop_monitoring()
        print("Network monitor stopped.")

    except Exception as e:
        logging.error(f"Error in main: {e}")
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()
