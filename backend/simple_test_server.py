#!/usr/bin/env python3
"""
simple_test_server.py
Simple test upload server for testing HTTP upload blocking

This server provides a basic web interface where you can upload real files
to test the DLP HTTP upload blocking functionality.
"""

from flask import Flask, request, render_template_string
import os
import time
from datetime import datetime
import requests
import re  # For CNIC regex

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'test_uploads'
ADMIN_SERVER_URL = "http://127.0.0.1:5000"
API_KEY = os.environ["DATASHIELD_API_KEY"]  # must match admin_server.py
LOG_FOLDER = "logs"
LOG_FILE = os.path.join(LOG_FOLDER, "upload_log.txt")

# Create required directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Simple Test Upload Server</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 600px; margin: 0 auto; }
        .upload-form { border: 2px dashed #ccc; padding: 20px; margin: 20px 0; }
        .file-input { margin: 10px 0; }
        .submit-btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .submit-btn:hover { background: #0056b3; }
        .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .instructions { background: #f8f9fa; padding: 15px; border-radius: 4px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 Simple Test Upload Server</h1>

        <div class="instructions">
            <h3>Testing Instructions:</h3>
            <ol>
                <li><strong>Upload files below</strong> to test the system</li>
                <li><strong>Check admin interface</strong> at <a href="http://127.0.0.1:5000" target="_blank">http://127.0.0.1:5000</a></li>
                <li><strong>Admin will decide</strong> to allow or block each upload</li>
                <li><strong>Refresh this page</strong> to see the admin's decision</li>
            </ol>
        </div>

        <div class="upload-form">
            <h2>Upload Test Files</h2>
            <form method="POST" action="/upload" enctype="multipart/form-data">
                <div class="file-input">
                    <label for="file">Select file to upload:</label><br>
                    <input type="file" id="file" name="file" required>
                </div>
                <button type="submit" class="submit-btn">Upload File</button>
            </form>
        </div>

        {% if message %}
        <div class="status" style="background: #28a745; color: white;">
            <strong>{{ message }}</strong>
        </div>
        {% endif %}

        <div class="upload-form">
            <h2>Upload History</h2>
            {% if uploads %}
                {% for upload in uploads %}
                <div class="status" style="background: {% if upload.status.startswith('ALLOWED') %}#28a745{% elif upload.status.startswith('BLOCKED') %}#dc3545{% else %}#17a2b8{% endif %}; color: white;">
                    <strong>{{ upload.filename }}</strong> -
                    {{ upload.status }} at {{ upload.timestamp }}
                </div>
                {% endfor %}
            {% else %}
                <p>No uploads yet.</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

upload_history = []

@app.route('/')
def index():
    """Display upload history and poll admin for updated decisions."""
    for upload in upload_history:
        if upload['status'] == 'PENDING ADMIN DECISION' and 'upload_id' in upload:
            try:
                upload_id = upload['upload_id']
                response = requests.get(
                    f"{ADMIN_SERVER_URL}/check_decision/{upload_id}",
                    headers={'X-API-KEY': API_KEY},
                    timeout=3
                )
                if response.status_code == 200:
                    result = response.json()
                    if result.get('status') == 'decided':
                        decision = result.get('decision')
                        if decision == 'allow':
                            upload['status'] = 'ALLOWED BY ADMIN'
                        elif decision == 'block':
                            upload['status'] = 'BLOCKED BY ADMIN'
            except Exception as e:
                print(f"[!] Error checking admin decision: {e}")
                pass

    return render_template_string(HTML_TEMPLATE, uploads=upload_history)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload, CNIC detection, notify admin, and log results."""
    if 'file' not in request.files:
        from flask import redirect, url_for
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        from flask import redirect, url_for
        return redirect(url_for('index'))

    if file:
        filename = file.filename
        file_ext = os.path.splitext(filename)[1].lower()
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        upload_id = f"upload_{int(time.time() * 1000)}"

        # --- CNIC detection ---
        CNIC_PATTERN = re.compile(r"\b\d{5}-\d{7}-\d\b")
        sensitive = False
        matches = []
        preview = None
        try:
            with open(filepath, "rb") as f:
                raw = f.read(2000)
            text = raw.decode("utf-8", errors="ignore")
            matches = CNIC_PATTERN.findall(text)
            if matches:
                sensitive = True
            preview = text[:800]
        except Exception as e:
            print(f"[!] CNIC scan error: {e}")
        # ----------------------

        # Notify admin
        alert_data = {
            "client": "simple_test_server",
            "filename": filename,
            "upload_url": f"http://127.0.0.1:8080/{UPLOAD_FOLDER}/{filename}",
            "file_type": file_ext,
            "process_name": "simple_test_server",
            "process_pid": os.getpid(),
            "upload_id": upload_id,
            "timestamp": datetime.now().isoformat(),
            "sensitive": sensitive,
            "sensitive_matches": matches,
            "preview": preview,
            "file_size": os.path.getsize(filepath)
        }
        headers = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}

        alert_status = "FAILED"
        try:
            r = requests.post(f"{ADMIN_SERVER_URL}/upload_alert", json=alert_data, headers=headers, timeout=5)
            if r.status_code == 200:
                alert_status = "SENT"
                print(f"[+] Alert sent to admin for file: {filename}")
            else:
                alert_status = f"ERROR {r.status_code}"
                print(f"[!] Admin responded with {r.status_code}: {r.text}")
        except Exception as e:
            alert_status = f"EXCEPTION {e}"
            print(f"[!] Failed to notify admin server: {e}")

        # --- Log upload attempt ---
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as log:
                log.write(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"File: {filename} | Sensitive: {sensitive} | CNICs: {', '.join(matches) if matches else 'None'} | "
                    f"Admin Alert: {alert_status}\n"
                )
        except Exception as e:
            print(f"[!] Logging failed: {e}")
        # --------------------------

        upload_history.append({
            "filename": filename,
            "status": "PENDING ADMIN DECISION",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "upload_id": upload_id
        })

        if len(upload_history) > 10:
            upload_history.pop(0)

        from flask import redirect, url_for
        return redirect(url_for('index'))

if __name__ == '__main__':
    print("🔒 Simple Test Upload Server")
    print("=" * 40)
    print("Server starting on http://127.0.0.1:8080")
    print("Upload files here to test HTTP upload blocking")
    print("=" * 40)

    app.run(host='127.0.0.1', port=8080, debug=True)
