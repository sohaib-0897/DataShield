# Manual Windows USB test

This checklist exercises the Windows event collector with a test device. Physical USB validation has not been performed as part of the repository checks. Use a disposable USB device and synthetic files only.

## Preparation

1. Start Docker Desktop and the local services from the repository root: `docker compose up --build -d`.
2. Confirm `Invoke-RestMethod http://localhost:8001/ready` returns `{"status":"ready"}`.
3. In a separate PowerShell window, enter the same `DATASHIELD_AGENT_KEY` configured in the ignored root `.env`, set the URL, and launch the agent:

   ```powershell
   $env:DATASHIELD_URL = 'http://localhost:8001'
   $env:DATASHIELD_AGENT_KEY = '<local agent key from .env>'
   python -m agents.usb
   ```

   Install `requirements-agents.txt` in the Python environment first. The USB collector supports Windows only. It sends device arrival/removal events and watches files created on an inserted drive; a transfer is observed as a destination file event, not a source-side copy operation.

## Device walkthrough

1. Insert the disposable USB device and wait for the agent to report a successful event delivery (or inspect the dashboard endpoint/event state).
2. Create a harmless file such as `normal-test.txt` containing `synthetic USB test content only` and copy it to the drive.
3. Create `sensitive-test.txt` in a temporary local folder with the synthetic text `Test identifier 12345-1234567-1` and copy it to the drive. Never use a real identifier or document.
4. Sign into <http://localhost:3001>. Inspect **Alerts** for an alert if the current risk policy crossed its threshold. Otherwise use authenticated `GET /api/v1/events` or the recent event view/API to confirm the `USB_FILE_TRANSFER` event and its masked detection evidence.
5. Inspect **System status** for the agent endpoint heartbeat. Check `docker compose logs backend` for service errors; routine request logs contain route/status/timing only.
6. Use Windows **Safely Remove Hardware** (or the OS eject action), wait for the device removal event, then physically disconnect it.

Expected records use the endpoint hostname, `USB_INSERT` / `USB_REMOVE`, and `USB_FILE_TRANSFER` for watched copied files. A sensitive rule match may contribute to an alert, but an alert is not guaranteed for every copy: policy thresholds and history affect the final risk. Do not interpret lack of an alert as lack of event ingestion.
