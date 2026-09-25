from flask import Flask, request, render_template_string, abort, jsonify, make_response
from flask_cors import CORS
from datetime import datetime
from pathlib import Path
import html
import re
import os
from types import SimpleNamespace
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from legacy.flask.database import session_scope
from legacy.flask.models import User, Event, Alert, AlertEvidence, AnalystDecision, AuditLog

app = Flask(__name__)
FRONTEND_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
if os.getenv('DATASHIELD_FRONTEND_ORIGIN'):
    FRONTEND_ORIGINS.append(os.environ['DATASHIELD_FRONTEND_ORIGIN'])

# Configure CORS to allow frontend requests
CORS(app,
     origins=FRONTEND_ORIGINS,
     allow_headers=["Content-Type", "X-API-KEY"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=True)

# Explicit CORS preflight handler for OPTIONS requests
@app.before_request
def handle_preflight():
    """Explicitly handle CORS preflight OPTIONS requests."""
    if request.method == "OPTIONS":
        response = make_response()
        response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-KEY"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "3600"
        return response, 200

# Add CORS headers to all responses
@app.after_request
def add_cors_headers(response):
    """Add CORS headers to all responses for cross-origin requests."""
    origin = request.headers.get('Origin', 'http://localhost:3000')
    if origin in FRONTEND_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    # Development-friendly CSP: allows unsafe-eval for webpack/React HMR
    # WARNING: Remove unsafe-eval in production!
    response.headers["Content-Security-Policy"] = "default-src *; script-src * 'unsafe-eval' 'unsafe-inline'; style-src * 'unsafe-inline';"
    return response

SECRET_API_KEY = os.environ["DATASHIELD_API_KEY"]
if not SECRET_API_KEY.strip():
    raise RuntimeError("DATASHIELD_API_KEY must not be empty")

# CNIC regex - used for inline highlighting when preview text available
CNIC_REGEX = re.compile(r"\b\d{5}-\d{7}-\d\b")

# Admin dashboard main page template
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Alerts</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 24px; }
        .section { margin-bottom: 30px; }
        .upload-alert { margin: 10px 0; padding: 12px; border: 1px solid #ddd; background:#fafafa; border-radius:6px; }
        .sensitive-badge { color: white; background: #dc3545; padding: 3px 8px; border-radius: 12px; font-weight: bold; font-size:12px; }
        .actions button { margin-right:8px; padding:6px 10px; border-radius:4px; border:none; cursor:pointer; }
        .btn-view { background:#17a2b8; color:white; }
        .btn-allow { background:#28a745; color:white; }
        .btn-block { background:#dc3545; color:white; }
        .btn-dismiss { background:#007bff; color:white; }
        a.link { text-decoration:none; color:#007bff; font-weight:600; }
    </style>
    <script>
        function viewUpload(alertId) {
            window.open('/view_file/' + alertId, '_blank', 'width=900,height=700');
        }
        function viewActivity(alertId) {
            window.open('/view_file_activity/' + alertId, '_blank', 'width=900,height=700');
        }
        async function sendDecision(alertId, decision) {
            const resp = await fetch('/upload_decision', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({alert_id: alertId, decision: decision})
            });
            if (resp.ok) {
                document.getElementById('upload-alert-' + alertId).remove();
            } else {
                alert('Failed to send decision');
            }
        }
        async function dismissActivity(alertId) {
            const resp = await fetch('/dismiss_file_activity', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({alert_id: alertId})
            });
            if (resp.ok) {
                document.getElementById('file-activity-' + alertId).remove();
            } else {
                alert('Failed to dismiss');
            }
        }
        async function clearAllActivities() {
            const resp = await fetch('/clear_all_file_activities', {method:'POST'});
            if (resp.ok) location.reload();
            else alert('Failed to clear');
        }
        // Auto-refresh
        setTimeout(()=>location.reload(), 10000);
    </script>
</head>
<body>
    <h1>Admin Dashboard</h1>

    <div class="section">
        <h2>File Activity Alerts</h2>
        {% if file_activity_alerts %}
            <button onclick="clearAllActivities()" style="background:#dc3545;color:white;padding:8px 12px;border-radius:6px;border:none;margin-bottom:10px;">Clear All Alerts</button>
            {% for aid, a in file_activity_alerts.items() %}
                <div class="upload-alert" id="file-activity-{{aid}}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <b>Client:</b> {{a.client}} &nbsp; | &nbsp;
                            <b>Activity:</b> {{a.activity}} &nbsp; | &nbsp;
                            <b>Filename:</b> {{a.filename}}
                            {% if a.sensitive %}
                                &nbsp; <span class="sensitive-badge">SENSITIVE</span>
                            {% endif %}
                            <br>
                            <small><b>Path:</b> {{a.file_path}}</small><br>
                            <small><b>Time:</b> {{a.timestamp}}</small>
                        </div>
                        <div class="actions">
                            <button class="btn-view" onclick="viewActivity({{aid}})">View</button>
                            <button class="btn-dismiss" onclick="dismissActivity({{aid}})">Dismiss</button>
                        </div>
                    </div>
                </div>
            {% endfor %}
        {% else %}
            <p>No file activity alerts yet.</p>
        {% endif %}
    </div>

    <div class="section">
        <h2>HTTP Upload Alerts (Approve / Block)</h2>
        {% if upload_alerts %}
            {% for aid, a in upload_alerts.items() %}
                <div class="upload-alert" id="upload-alert-{{aid}}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <b>Client:</b> {{a.client}} &nbsp; | &nbsp;
                            <b>Filename:</b> {{a.filename}}
                            {% if a.sensitive %}
                                &nbsp; <span class="sensitive-badge">SENSITIVE</span>
                            {% endif %}
                            <br>
                            <small><b>Upload URL:</b> {{a.upload_url}}</small><br>
                            <small><b>Time:</b> {{a.timestamp}}</small>
                        </div>
                        <div class="actions">
                            <button class="btn-view" onclick="viewUpload({{aid}})">View</button>
                            <button class="btn-allow" onclick="sendDecision({{aid}}, 'allow')">Allow</button>
                            <button class="btn-block" onclick="sendDecision({{aid}}, 'block')">Block</button>
                        </div>
                    </div>
                </div>
            {% endfor %}
        {% else %}
            <p>No HTTP upload alerts pending.</p>
        {% endif %}
    </div>

    <div class="section">
        <h2>Allowed Uploads</h2>
        {% if allowed_uploads %}
            <p>{{allowed_uploads|length}} files approved. <a href="/allowed_uploads" class="link">View all</a></p>
        {% else %}
            <p>No allowed uploads yet.</p>
        {% endif %}
    </div>

</body>
</html>
"""

def require_api_key(req):
    api_key = req.headers.get("X-API-KEY")
    return api_key == SECRET_API_KEY


def _alert_object(alert):
    payload = dict.fromkeys(('client', 'filename', 'upload_url', 'file_type', 'process_name',
                             'process_pid', 'upload_id', 'file_size', 'activity', 'file_path',
                             'new_path', 'modified_time'))
    payload.update(alert.event.payload)
    payload.update(timestamp=alert.event.timestamp,
                   sensitive=alert.evidence.sensitive if alert.evidence else False,
                   sensitive_matches=alert.evidence.matches if alert.evidence else [],
                   preview=alert.evidence.preview if alert.evidence else None)
    return SimpleNamespace(**payload)


def _pending(session, kind):
    rows = session.scalars(select(Alert).join(Event).where(
        Event.kind == kind, Alert.status == 'pending').options(
        joinedload(Alert.event), joinedload(Alert.evidence)).order_by(Alert.id)).unique().all()
    return {row.id: _alert_object(row) for row in rows}


def _allowed_uploads(session):
    rows = session.scalars(select(AnalystDecision).join(Alert).join(Event).where(
        Event.kind == 'upload', AnalystDecision.decision == 'allow').options(
        joinedload(AnalystDecision.alert).joinedload(Alert.event)).order_by(AnalystDecision.id)).all()
    return [dict(filename=row.alert.event.payload.get('filename'),
                 file_type=row.alert.event.payload.get('file_type') or 'Unknown',
                 client=row.alert.event.payload.get('client'),
                 upload_url=row.alert.event.payload.get('upload_url', 'unknown'),
                 timestamp=row.timestamp[:19].replace('T', ' '), upload_id=row.upload_id)
            for row in rows]


def _audit(session, action, alert_id=None, details=None):
    session.add(AuditLog(action=action, alert_id=alert_id, details=details or {}))


def _create_alert(kind, data):
    timestamp = data.get('timestamp') or datetime.now().isoformat()
    with session_scope() as session:
        client = data.get('client')
        user = session.scalar(select(User).where(User.name == client)) if client else None
        if client and user is None:
            user = User(name=client)
            session.add(user)
            session.flush()
        event = Event(user_id=user.id if user else None, kind=kind,
                      payload={key: value for key, value in data.items()
                               if key not in ('preview', 'sensitive_matches', 'sensitive', 'timestamp')},
                      timestamp=timestamp)
        alert = Alert(event=event, evidence=AlertEvidence(
            preview=data.get('preview'), sensitive=bool(data.get('sensitive', False)),
            matches=data.get('sensitive_matches') or []))
        session.add(alert)
        session.flush()
        _audit(session, 'alert_created', alert.id, {'kind': kind})
        return alert.id

@app.route('/')
def home():
    with session_scope() as session:
        return render_template_string(HTML_PAGE,
                                      upload_alerts=_pending(session, 'upload'),
                                      file_activity_alerts=_pending(session, 'file_activity'),
                                      allowed_uploads=_allowed_uploads(session))

@app.route('/upload_alert', methods=['POST'])
def receive_upload_alert():
    if not require_api_key(request):
        abort(401)
    data = request.json or {}
    _create_alert('upload', data)
    return "Upload alert received", 200

@app.route('/file_activity_alert', methods=['POST'])
def receive_file_activity_alert():
    if not require_api_key(request):
        abort(401)
    data = request.json or {}

    # Expecting an 'activity' field for file activity alerts
    if 'activity' in data:
        _create_alert('file_activity', data)
        return "File activity alert received", 200
    else:
        # Backwards compat: treat as upload alert if no 'activity'
        return receive_upload_alert()

@app.route('/upload_decision', methods=['POST'])
def upload_decision():
    """
    Handle analyst decision (allow/block) for alerts.
    Works with both upload_alerts and file_activity_alerts.
    """
    data = request.json or {}
    alert_id = data.get("alert_id")
    decision = data.get("decision")

    if alert_id is None or decision not in ('allow', 'block'):
        return jsonify({"error": "Invalid request"}), 400

    with session_scope() as session:
        alert = session.get(Alert, alert_id, options=[joinedload(Alert.event)])
        if alert is None or alert.status != 'pending':
            return jsonify({"error": "Alert not found"}), 404
        timestamp = datetime.now().isoformat()
        if alert.event.kind == 'upload':
            upload_id = alert.event.payload.get('upload_id') or str(alert_id)
            alert.status = 'decided'
            session.add(AnalystDecision(alert_id=alert_id, upload_id=upload_id,
                                        decision=decision, timestamp=timestamp))
            _audit(session, 'upload_decision', alert_id, {'decision': decision, 'upload_id': upload_id})
            return jsonify({"status": "success", "decision": decision, "alert_id": alert_id,
                            "alert_type": "upload", "upload_id": upload_id, "timestamp": timestamp})
        session.add(AnalystDecision(alert_id=alert_id, decision=decision, timestamp=timestamp))
        _audit(session, 'file_activity_decision', alert_id, {'decision': decision})
        return jsonify({"status": "success", "decision": decision, "alert_id": alert_id,
                        "alert_type": "file_activity", "activity": alert.event.payload.get('activity'),
                        "timestamp": timestamp})

@app.route('/pending_decisions', methods=['GET'])
def get_pending_decisions():
    if not require_api_key(request):
        abort(401)
    with session_scope() as session:
        rows = session.scalars(select(AnalystDecision).where(
            AnalystDecision.upload_id.is_not(None)).order_by(AnalystDecision.id)).all()
        return jsonify({row.upload_id: row.decision for row in rows})

@app.route('/check_decision/<upload_id>', methods=['GET'])
def check_decision(upload_id):
    if not require_api_key(request):
        abort(401)
    with session_scope() as session:
        row = session.scalar(select(AnalystDecision).where(
            AnalystDecision.upload_id == upload_id).order_by(AnalystDecision.id.desc()))
    if row:
        return jsonify({"status": "decided", "decision": row.decision})
    return jsonify({"status": "pending"})

@app.route('/alerts', methods=['GET'])
def get_alerts():
    """
    Get all pending alerts (both upload and file activity)
    Returns both types combined with 'type' field to distinguish them
    """
    if not require_api_key(request):
        abort(401)

    alerts = []

    with session_scope() as session:
        upload_alerts = _pending(session, 'upload')
        file_activity_alerts = _pending(session, 'file_activity')

    # Add upload alerts (these are file upload attempts)
    for alert_id, alert in upload_alerts.items():
        alert_dict = {
            "id": alert_id,
            "type": "upload",
            "user": alert.client,
            "timestamp": alert.timestamp,
            "channel": "cloud",  # Upload alerts are typically cloud uploads
            "riskScore": 85,  # Default risk score - could be enhanced if agent sends it
            "severity": "high" if alert.sensitive else "medium",  # Based on sensitivity
            "status": "pending",
            "activity": f"Upload attempt to {(getattr(alert, 'upload_url', None) or 'unknown').split('/')[-1]}",
            "file": alert.filename,
            "fileSize": alert.file_size or "unknown",
            "isSensitive": alert.sensitive,
            "sensitiveMatches": alert.sensitive_matches or [],
        }
        alerts.append(alert_dict)

    # Add file activity alerts (file system operations)
    for alert_id, alert in file_activity_alerts.items():
        alert_dict = {
            "id": alert_id,
            "type": "file_activity",
            "user": alert.client,
            "timestamp": alert.timestamp,
            "channel": "file",  # File activity is local file operations
            "riskScore": 75,  # Default risk score
            "severity": "high" if alert.sensitive else "medium",
            "status": "pending",
            "activity": alert.activity,
            "file": alert.filename,
            "filePath": alert.file_path,
            "fileSize": alert.file_size or "unknown",
            "isSensitive": alert.sensitive,
            "sensitiveMatches": alert.sensitive_matches or [],
        }
        alerts.append(alert_dict)

    # Sort by timestamp descending (newest first)
    alerts.sort(key=lambda x: x["timestamp"], reverse=True)

    return jsonify(alerts)

@app.route('/dismiss_file_activity', methods=['POST'])
def dismiss_file_activity():
    data = request.json or {}
    alert_id = data.get("alert_id")
    if alert_id is None:
        return jsonify({"error": "Invalid request"}), 400
    with session_scope() as session:
        alert = session.get(Alert, alert_id, options=[joinedload(Alert.event)])
        if alert is None or alert.status != 'pending' or alert.event.kind != 'file_activity':
            return jsonify({"error": "Alert not found"}), 404
        alert.status = 'dismissed'
        _audit(session, 'file_activity_dismissed', alert_id)
    return jsonify({"status": "dismissed"})

@app.route('/clear_all_file_activities', methods=['POST'])
def clear_all_file_activities():
    with session_scope() as session:
        rows = session.scalars(select(Alert).join(Event).where(
            Event.kind == 'file_activity', Alert.status == 'pending')).all()
        for alert in rows:
            alert.status = 'dismissed'
            _audit(session, 'file_activity_dismissed', alert.id, {'source': 'clear_all'})
    return jsonify({"status": "cleared"})

def _highlight_cnic_in_html(text: str):
    """
    Replace CNIC occurrences with HTML-highlighted span.
    We HTML-escape the text first, then replace the escaped matches.
    """
    if not text:
        return ""
    # Escape text to avoid HTML injection, then highlight the CNICs
    escaped = html.escape(text)
    # CNIC regex will match on the escaped form because digits/hyphens are unchanged
    def repl(m):
        matched = m.group(0)
        return f'<span style="color:red;font-weight:bold;">{matched}</span>'
    highlighted = CNIC_REGEX.sub(repl, escaped)
    # Convert newlines to <br> for display
    highlighted = highlighted.replace("\n", "<br>")
    return highlighted

@app.route('/view_file/<int:alert_id>')
def view_file(alert_id):
    """
    View details for an upload alert (HTTP upload).
    Uses preview if available; otherwise attempts to read file from test_uploads (if present).
    """
    with session_scope() as session:
        alert = _pending(session, 'upload').get(alert_id)
    if alert is None:
        return "<html><body><h2>Upload alert not found</h2></body></html>", 404

    # Use preview if agent provided one
    preview_text = None
    if hasattr(alert, "preview") and alert.preview:
        preview_text = alert.preview
    else:
        # Try to load file from test_uploads folder if upload_url points to local test storage
        try:
            fp = Path("test_uploads") / alert.filename
            if fp.exists():
                raw = fp.read_bytes()
                try:
                    preview_text = raw.decode("utf-8", errors="ignore")[:2000]
                except Exception:
                    preview_text = None
        except Exception:
            preview_text = None

    highlighted = _highlight_cnic_in_html(preview_text) if preview_text else "<i>No preview available.</i>"

    # Prepare metadata
    file_size = getattr(alert, "file_size", None)
    sensitive = getattr(alert, "sensitive", False)
    matches = getattr(alert, "sensitive_matches", []) or []

    html_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>View Upload - {html.escape(alert.filename or 'file')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background:#007bff;color:white;padding:12px;border-radius:6px; }}
            .meta {{ margin-top:10px; padding:10px; background:#f5f5f5; border-radius:6px; }}
            pre.preview {{ white-space:pre-wrap; padding:12px; background:#fff; border:1px solid #ddd; border-radius:6px; max-height:520px; overflow:auto; }}
            .sensitive-list {{ background:#fff6f6; border:1px solid #ffdede; padding:8px; border-radius:6px; margin-top:8px; }}
        </style>
    </head>
    <body>
        <div class="header"><h2>File: {html.escape(alert.filename or '')}</h2></div>
        <div class="meta">
            <b>Client:</b> {html.escape(str(alert.client or ''))} <br>
            <b>Upload URL:</b> {html.escape(str(alert.upload_url or ''))} <br>
            <b>File size:</b> {html.escape(str(file_size or 'Unknown'))} <br>
            <b>Timestamp:</b> {html.escape(str(alert.timestamp or ''))} <br>
            <b>Sensitive:</b> {'<span style="color:red;font-weight:bold;">YES</span>' if sensitive else 'No'}
        </div>

        <h3>Preview (CNICs highlighted)</h3>
        <div class="preview">{highlighted}</div>

        <h3>Detected CNICs</h3>
        <div class="sensitive-list">
            {"<br>".join([html.escape(m) for m in matches]) if matches else "<i>None detected</i>"}
        </div>

        <p><button onclick="window.close()" style="padding:8px 12px;border-radius:6px;border:none;background:#dc3545;color:white;">Close</button></p>
    </body>
    </html>
    """
    return html_page

@app.route('/view_file_activity/<int:alert_id>')
def view_file_activity(alert_id):
    """
    View details for a file activity alert (created/modified/moved).
    Uses provided preview and highlights CNICs inline.
    """
    with session_scope() as session:
        alert = _pending(session, 'file_activity').get(alert_id)
    if alert is None:
        return "<html><body><h2>File activity alert not found</h2></body></html>", 404
    preview_text = getattr(alert, "preview", None)
    highlighted = _highlight_cnic_in_html(preview_text) if preview_text else "<i>No preview available.</i>"

    file_size = getattr(alert, "file_size", None)
    modified_time = getattr(alert, "modified_time", None)
    sensitive = getattr(alert, "sensitive", False)
    matches = getattr(alert, "sensitive_matches", []) or []

    html_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>View File Activity - {html.escape(alert.filename or '')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background:#007bff;color:white;padding:12px;border-radius:6px; }}
            .meta {{ margin-top:10px; padding:10px; background:#f5f5f5; border-radius:6px; }}
            pre.preview {{ white-space:pre-wrap; padding:12px; background:#fff; border:1px solid #ddd; border-radius:6px; max-height:520px; overflow:auto; }}
            .sensitive-list {{ background:#fff6f6; border:1px solid #ffdede; padding:8px; border-radius:6px; margin-top:8px; }}
        </style>
    </head>
    <body>
        <div class="header"><h2>File: {html.escape(alert.filename or '')}</h2></div>
        <div class="meta">
            <b>Client:</b> {html.escape(str(alert.client or ''))} <br>
            <b>Activity:</b> {html.escape(str(alert.activity or ''))} <br>
            <b>Path:</b> {html.escape(str(alert.file_path or ''))} <br>
            <b>New Path:</b> {html.escape(str(alert.new_path or ''))} <br>
            <b>File size:</b> {html.escape(str(file_size or 'Unknown'))} <br>
            <b>Modified:</b> {html.escape(str(modified_time or 'Unknown'))} <br>
            <b>Timestamp:</b> {html.escape(str(alert.timestamp or ''))} <br>
            <b>Sensitive:</b> {'<span style="color:red;font-weight:bold;">YES</span>' if sensitive else 'No'}
        </div>

        <h3>Preview (CNICs highlighted)</h3>
        <div class="preview">{highlighted}</div>

        <h3>Detected CNICs</h3>
        <div class="sensitive-list">
            {"<br>".join([html.escape(m) for m in matches]) if matches else "<i>None detected</i>"}
        </div>

        <p><button onclick="window.close()" style="padding:8px 12px;border-radius:6px;border:none;background:#dc3545;color:white;">Close</button></p>
    </body>
    </html>
    """
    return html_page

@app.route('/allowed_uploads')
def view_allowed_uploads():
    ALLOWED_UPLOADS_PAGE = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Allowed Uploads</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 24px; }
            table { width:100%; border-collapse: collapse; margin-top:10px; }
            th, td { padding:12px; border-bottom:1px solid #eee; text-align:left; }
            th { background:#28a745; color:white; }
            .back { display:inline-block; margin-bottom:10px; padding:8px 10px; background:#007bff; color:white; border-radius:6px; text-decoration:none; }
        </style>
    </head>
    <body>
        <a href="/" class="back">← Back to Dashboard</a>
        <h2>Allowed Uploads ({{allowed_uploads|length}})</h2>
        {% if allowed_uploads %}
            <table>
                <thead><tr><th>Filename</th><th>File Type</th><th>Client</th><th>Timestamp</th><th>Action</th></tr></thead>
                <tbody>
                    {% for u in allowed_uploads %}
                        <tr>
                            <td>{{u.filename}}</td>
                            <td>{{u.file_type}}</td>
                            <td>{{u.client}}</td>
                            <td>{{u.timestamp}}</td>
                            <td><a href="{{u.upload_url}}" target="_blank">View Source</a></td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% else %}
            <p>No allowed uploads yet.</p>
        {% endif %}
    </body>
    </html>
    """
    with session_scope() as session:
        return render_template_string(ALLOWED_UPLOADS_PAGE, allowed_uploads=_allowed_uploads(session))

# ============================================================================
# User Activity API Endpoints
# ============================================================================

@app.route('/api/users/activity', methods=['GET'])
def get_user_activity():
    """
    Get user activity data for the UserActivity dashboard
    Returns user list with risk scores, trends, and anomalies
    """
    if not require_api_key(request):
        abort(401)

    # Mock user data that matches frontend expectations
    mock_users = [
        {
            "id": 1,
            "email": "john.doe@company.com",
            "riskScore": 85,
            "status": "high-risk",
            "lastActivity": "2 minutes ago",
            "alertCount": 7,
            "activities": [
                {"time": "Mon", "suspicious": 5, "normal": 15},
                {"time": "Tue", "suspicious": 6, "normal": 14},
                {"time": "Wed", "suspicious": 7, "normal": 13},
                {"time": "Thu", "suspicious": 6, "normal": 14},
                {"time": "Fri", "suspicious": 8, "normal": 12},
                {"time": "Sat", "suspicious": 2, "normal": 8},
                {"time": "Sun", "suspicious": 2, "normal": 8},
            ],
        },
        {
            "id": 2,
            "email": "jane.smith@company.com",
            "riskScore": 62,
            "status": "medium-risk",
            "lastActivity": "15 minutes ago",
            "alertCount": 3,
            "activities": [
                {"time": "Mon", "suspicious": 2, "normal": 18},
                {"time": "Tue", "suspicious": 3, "normal": 16},
                {"time": "Wed", "suspicious": 4, "normal": 14},
                {"time": "Thu", "suspicious": 3, "normal": 17},
                {"time": "Fri", "suspicious": 5, "normal": 15},
                {"time": "Sat", "suspicious": 1, "normal": 8},
                {"time": "Sun", "suspicious": 1, "normal": 6},
            ],
        },
        {
            "id": 3,
            "email": "bob.wilson@company.com",
            "riskScore": 34,
            "status": "low-risk",
            "lastActivity": "1 hour ago",
            "alertCount": 1,
            "activities": [
                {"time": "Mon", "suspicious": 0, "normal": 22},
                {"time": "Tue", "suspicious": 0, "normal": 20},
                {"time": "Wed", "suspicious": 1, "normal": 18},
                {"time": "Thu", "suspicious": 0, "normal": 21},
                {"time": "Fri", "suspicious": 0, "normal": 19},
                {"time": "Sat", "suspicious": 0, "normal": 10},
                {"time": "Sun", "suspicious": 0, "normal": 8},
            ],
        },
    ]

    user_risk_trend_data = [
        {"week": "Wk 1", "john": 65, "jane": 45, "bob": 20},
        {"week": "Wk 2", "john": 72, "jane": 52, "bob": 22},
        {"week": "Wk 3", "john": 78, "jane": 58, "bob": 25},
        {"week": "Wk 4", "john": 85, "jane": 62, "bob": 28},
        {"week": "Wk 5", "john": 92, "jane": 67, "bob": 34},
    ]

    anomalies = [
        {
            "id": 1,
            "user": "john.doe@company.com",
            "anomaly": "Unusual file access pattern",
            "severity": "high",
            "timestamp": "2 hours ago",
        },
        {
            "id": 2,
            "user": "jane.smith@company.com",
            "anomaly": "Off-hours activity detected",
            "severity": "medium",
            "timestamp": "5 hours ago",
        },
        {
            "id": 3,
            "user": "bob.wilson@company.com",
            "anomaly": "Abnormal data download volume",
            "severity": "low",
            "timestamp": "1 day ago",
        },
    ]

    return jsonify({
        "users": mock_users,
        "userRiskTrend": user_risk_trend_data,
        "anomalies": anomalies,
    })

# ============================================================================
# Reports API Endpoints
# ============================================================================

@app.route('/api/reports/summary', methods=['GET'])
def get_reports_summary():
    """
    Get summary statistics for the Reports dashboard
    Returns key metrics and incident data
    """
    if not require_api_key(request):
        abort(401)

    return jsonify({
        "totalIncidents": 847,
        "totalIncidentsChange": "+12%",
        "incidentsBlocked": 156,
        "incidentsBlockedPercentage": 18.4,
        "investigated": 342,
        "investigatedPercentage": 40.4,
        "avgResponseTime": "2.4h",
    })

@app.route('/api/reports/alerts', methods=['GET'])
def get_alert_trends():
    """
    Get alert trends data for the Reports dashboard
    Returns daily alert counts and blocked counts
    """
    if not require_api_key(request):
        abort(401)

    alert_trends_data = [
        {"date": "Mon", "alerts": 145, "blocked": 28},
        {"date": "Tue", "alerts": 152, "blocked": 31},
        {"date": "Wed", "alerts": 134, "blocked": 24},
        {"date": "Thu", "alerts": 167, "blocked": 35},
        {"date": "Fri", "alerts": 156, "blocked": 29},
        {"date": "Sat", "alerts": 98, "blocked": 18},
        {"date": "Sun", "alerts": 89, "blocked": 15},
    ]

    return jsonify(alert_trends_data)

@app.route('/api/reports/threats', methods=['GET'])
def get_threat_analysis():
    """
    Get threat analysis data for the Reports dashboard
    Returns top threats and their classifications
    """
    if not require_api_key(request):
        abort(401)

    top_threats_data = [
        {"name": "Data Exfiltration", "count": 234, "percentage": 28, "severity": "critical"},
        {"name": "Malware Detection", "count": 189, "percentage": 22, "severity": "high"},
        {"name": "Unauthorized Access", "count": 156, "percentage": 18, "severity": "high"},
        {"name": "Policy Violation", "count": 145, "percentage": 17, "severity": "medium"},
        {"name": "Suspicious Login", "count": 87, "percentage": 10, "severity": "medium"},
        {"name": "Network Anomaly", "count": 36, "percentage": 5, "severity": "low"},
    ]

    return jsonify(top_threats_data)

@app.route('/api/reports/users', methods=['GET'])
def get_user_reports():
    """
    Get user risk report data for the Reports dashboard
    Returns department risk analysis and user rankings
    """
    if not require_api_key(request):
        abort(401)

    department_risk_data = [
        {"department": "Finance", "risk": 78, "users": 45, "incidents": 156},
        {"department": "HR", "risk": 52, "users": 30, "incidents": 87},
        {"department": "IT", "risk": 45, "users": 28, "incidents": 64},
        {"department": "Marketing", "risk": 38, "users": 22, "incidents": 45},
        {"department": "Sales", "risk": 65, "users": 50, "incidents": 127},
        {"department": "Operations", "risk": 55, "users": 35, "incidents": 89},
    ]

    user_reports = [
        {
            "id": 1,
            "email": "john.doe@company.com",
            "department": "Finance",
            "riskScore": 92,
            "incidents": 12,
            "severity": "critical",
        },
        {
            "id": 2,
            "email": "jane.smith@company.com",
            "department": "Sales",
            "riskScore": 78,
            "incidents": 8,
            "severity": "high",
        },
        {
            "id": 3,
            "email": "bob.wilson@company.com",
            "department": "IT",
            "riskScore": 34,
            "incidents": 2,
            "severity": "low",
        },
    ]

    return jsonify({
        "departmentRisk": department_risk_data,
        "topUsers": user_reports,
    })

if __name__ == "__main__":
    # Run admin server
    app.run(host=os.getenv("DATASHIELD_HOST", "127.0.0.1"), port=5000)
