"""Browser connection metadata collector. A connection does not imply upload."""
import logging
import time

import psutil

from .common import event, heartbeat, send

LOG = logging.getLogger(__name__)
BROWSERS = {"chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "chrome", "firefox"}


def connections():
    for process in psutil.process_iter(["name", "pid"]):
        try:
            if (process.info["name"] or "").lower() not in BROWSERS:
                continue
            for connection in process.net_connections(kind="tcp"):
                if connection.status == psutil.CONN_ESTABLISHED and connection.raddr and connection.raddr.port in (80, 443):
                    yield process.info["pid"], process.info["name"], connection.raddr.ip, connection.raddr.port
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue


def main():
    logging.basicConfig(level=logging.INFO)
    observed = set()
    last_heartbeat = 0
    while True:
        if time.monotonic() - last_heartbeat > 60:
            try:
                heartbeat()
            except Exception as exc:
                LOG.warning("Heartbeat failed: %s", type(exc).__name__)
            last_heartbeat = time.monotonic()
        current = set(connections())
        for pid, name, ip, port in current - observed:
            try:
                send(event("NETWORK", "NETWORK_CONNECTION", f"{ip}:{port}", {"process_name": name, "remote_port": port}))
            except Exception as exc:
                LOG.error("Connection delivery failed: %s", type(exc).__name__)
        observed = current
        time.sleep(10)


if __name__ == "__main__": main()
