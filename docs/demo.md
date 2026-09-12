# Local demo with synthetic data

Start the API and frontend as described in the root README. In a new PowerShell terminal, set the same demo key and submit this synthetic event:

```powershell
$env:DATASHIELD_API_KEY = 'replace-with-your-local-demo-key'
$headers = @{ 'X-API-KEY' = $env:DATASHIELD_API_KEY }
$body = @{
    client = 'demo-workstation'
    filename = 'synthetic-record.txt'
    upload_id = 'demo-upload-001'
    upload_url = 'https://example.com/upload'
    file_type = '.txt'
    sensitive = $true
    sensitive_matches = @('00000-0000000-0')
    preview = 'Synthetic identifier: 00000-0000000-0'
} | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:5000/upload_alert -Method Post -Headers $headers -ContentType 'application/json' -Body $body
```

1. Open **Alerts** in the dashboard and locate `synthetic-record.txt`.
2. Open its investigation to inspect the supplied metadata and sensitive match.
3. Submit an allow or block decision.
4. Confirm the result through the polling endpoint:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/check_decision/demo-upload-001 -Headers $headers
```

This demonstrates an API approval round trip. It does not upload a real file or demonstrate network-wide enforcement. Restarting the API clears the demonstration state. Reports and User Activity contain sample analytics rather than measurements of this event.
