"""
DataShield console server. Same folder as your other scripts + dashboard.html.
    python dashboard.py   ->  http://127.0.0.1:8000
"""
import os, sys, csv, io, json, math, sqlite3, subprocess, platform
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory, Response

from behavior import get_behavior
from risk_engine import calculate_dlp_score, get_risk_level
from database import initialize_database, initialize_transfer_table
from sensitivity import SENSITIVE_FILES

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "data", "activity.db")
app = Flask(__name__)

MONITORS = {
    "files":    ("windows_monitor.py", "File access", "Windows Security log (run as Administrator)"),
    "usb":      ("usb_monitor.py", "USB devices", "Plug and unplug events"),
    "usbcopy":  ("usb_copy_monitor.py", "USB transfers", "Sensitive files copied to a USB drive"),
    "local":    ("local_copy_monitor.py", "Local copies", "Sensitive files duplicated on this device"),
    "drive":    ("google_drive_monitor.py", "Cloud sync", "Google Drive uploads"),
    "upload":   ("upload_server.py", "Web upload gateway", "Test server on port 5000"),
    "behavior": ("behavioral_monitor.py", "User behavior", "Active app and idle time"),
}
procs = {}
RULES = [
    ("R01", "Sensitive file copied to removable media", "USB transfer agent (SHA-256 match)", "Critical or High", "A.7.10, A.8.12", "Removable media is the simplest way to take data off-site without leaving a network trace."),
    ("R02", "Sensitive file synced to cloud storage", "Google Drive agent (SHA-256 match)", "Critical or High", "A.5.14, A.8.12", "Personal or unapproved cloud storage puts company data outside organisational control."),
    ("R03", "Sensitive file uploaded to a web service", "Upload gateway (SHA-256 match)", "Critical or High", "A.5.14, A.8.12", "Web uploads are a common exfiltration channel."),
    ("R04", "Sensitive file duplicated on the device", "Local copy agent (SHA-256 match)", "Medium", "A.5.10, A.8.3", "A copy escapes the access controls of the original location and often precedes exfiltration."),
    ("R05", "Protected file moved or renamed", "Folder watcher (watchdog)", "Medium (High, Critical files)", "A.5.14, A.8.3", "Moving data out of its protected location bypasses its access controls, even for permitted roles."),
    ("R06", "Unauthorised access to a protected file", "Events 4663, 4660 + role policy", "Medium to Critical", "A.5.15, A.5.18, A.8.3", "Least privilege: opening, editing or deleting a file outside your role is alerted. Access your role permits raises no alert."),
    ("R07", "Out-of-hours escalation", "Alert time vs working-hours setting", "Raises severity one level", "A.8.16", "Out-of-hours activity is a standard insider-threat indicator, so any alert outside working hours is escalated."),
    ("R08", "USB storage device connected", "WMI drive detection", "Low", "A.7.10", "Gives context: a later transfer to USB is correlated with the connection."),
]
RULE_OF = {"SENSITIVE_USB_COPY": "R01", "SENSITIVE_CLOUD_COPY": "R02", "SENSITIVE_UPLOAD": "R03", "SENSITIVE_LOCAL_COPY": "R04"}
EXTERNAL = {"SENSITIVE_USB_COPY", "SENSITIVE_CLOUD_COPY", "SENSITIVE_UPLOAD"}
CATS = {"files": {"FILE_READ", "FILE_WRITE", "FILE_DELETE", "MODIFIED", "CREATED", "DELETED", "MOVED"},
        "usb": {"USB_INSERTED", "USB_REMOVED", "SENSITIVE_USB_COPY"},
        "cloud": {"SENSITIVE_CLOUD_COPY", "SENSITIVE_UPLOAD", "SENSITIVE_LOCAL_COPY"}}


def db():
    con = sqlite3.connect(DB_PATH); con.row_factory = sqlite3.Row
    return con


def ensure_tables():
    initialize_database(); initialize_transfer_table()
    con = db()
    con.execute("""CREATE TABLE IF NOT EXISTS behavior_events (id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT, username TEXT, event_type TEXT, application TEXT, window_title TEXT, idle_seconds INTEGER)""")
    con.execute("CREATE TABLE IF NOT EXISTS alert_state (alert_id TEXT PRIMARY KEY, status TEXT, updated TEXT)")
    con.commit(); con.close()


def cutoff(minutes):
    return (datetime.now() - timedelta(minutes=minutes)).isoformat()


WEIGHT = {"CRITICAL": 25, "HIGH": 15, "MEDIUM": 6, "LOW": 1}
HALF_LIFE_H = 6          # an alert's influence halves every 6 hours
FACTOR = {"open": 1, "suspicious": 2}   # approved / auto_approved count as 0
POLICY_PATH = os.path.join(HERE, "data", "policy.json")
DEFAULT_POLICY = {"roles": {
    "Finance": ["salary.xlsx"], "HR": ["employee_records.txt", "salary.xlsx"],
    "Management": ["company_strategy.docx"], "Customer Support": ["customer_data.txt"],
    "Administrator": ["employee_records.txt", "salary.xlsx", "company_strategy.docx", "customer_data.txt"]}, "assign": {}, "disabled_rules": [],
    "settings": {"work_start": 9, "work_end": 17, "half_life_h": 6, "saturation": 50, "flag_floor": 60, "auto_approve": True}}


def load_policy():
    base = json.loads(json.dumps(DEFAULT_POLICY))
    try:
        pol = json.load(open(POLICY_PATH))
    except (OSError, ValueError):
        save_policy(base); return base
    for k, v in base.items(): pol.setdefault(k, v)
    for k, v in base["settings"].items(): pol["settings"].setdefault(k, v)
    return pol


def save_policy(pol):
    os.makedirs(os.path.dirname(POLICY_PATH), exist_ok=True)
    json.dump(pol, open(POLICY_PATH, "w"), indent=2)


def auto_decide(x, pol):
    """Routine, role-permitted access is approved automatically. Transfers out,
    deletions and after-hours access always go to a human."""
    S = pol["settings"]
    if not S["auto_approve"]:
        return "open", ""
    if x["title"] == "USB device connected":
        return "auto_approved", "Informational event. USB connections are logged but need no review."
    role = pol["assign"].get(x["user"])
    if role and x["title"].startswith("Critical file"):
        name = os.path.basename(x["file"]).lower()
        if name in [f.lower() for f in pol["roles"].get(role, [])] and S["work_start"] <= datetime.fromisoformat(x["ts"]).hour < S["work_end"]:
            return "auto_approved", f"The {role} role is allowed to use {name} during working hours."
    return "open", ""


def alert_load(alerts, use_status=True):
    now, tot, hl = datetime.now(), 0, load_policy()["settings"]["half_life_h"]
    for a in alerts:
        age = (now - datetime.fromisoformat(a["ts"])).total_seconds() / 3600
        f = FACTOR.get(a["status"], 0) if use_status else 1
        tot += WEIGHT[a["severity"]] * f * 0.5 ** (age / hl)
    return tot


def to_score(load):
    """Smooth saturating curve: scores climb gradually and never jump straight to 100."""
    return round(100 * (1 - math.exp(-load / load_policy()["settings"]["saturation"])))


def score_for(user, minutes, alerts=()):
    b = get_behavior(user, minutes)
    raw, s = to_score(alert_load(alerts, False)), to_score(alert_load(alerts))
    if any(a["status"] == "suspicious" for a in alerts):
        s = max(s, load_policy()["settings"]["flag_floor"])  # a flagged user is never below the floor
    return s, get_risk_level(s), b, raw


def build_alerts(minutes, user=None, permitted=False):
    con = db(); c = cutoff(minutes); out = []
    _S = load_policy()["settings"]; WS, WE = _S["work_start"], _S["work_end"]
    q, a = " AND username=?" if user else "", ((c, user) if user else (c,))
    for r in con.execute(f"SELECT * FROM transfers WHERE timestamp>=?{q} ORDER BY id DESC LIMIT 300", a):
        ext = r["event_type"] in EXTERNAL
        sev = ("CRITICAL" if r["sensitivity"] == "CRITICAL" else "HIGH") if ext else "MEDIUM"
        title = {"SENSITIVE_USB_COPY": "Sensitive file copied to USB", "SENSITIVE_CLOUD_COPY": "Sensitive file sent to Google Drive",
                 "SENSITIVE_UPLOAD": "Sensitive file uploaded to web", "SENSITIVE_LOCAL_COPY": "Sensitive file copied locally"}.get(r["event_type"], r["event_type"])
        out.append(dict(rule=RULE_OF.get(r["event_type"], "R04"), id=f"T{r['id']}", ts=r["timestamp"], user=r["username"], severity=sev, title=title,
                        file=r["source_path"], detail=f"{r['sensitivity']} file to {r['destination_type']}: {r['destination_path']}"))
    pol = load_policy(); S = pol["settings"]
    ACT = {"FILE_READ": "opened", "FILE_WRITE": "edited", "MODIFIED": "edited", "FILE_DELETE": "deleted", "DELETED": "deleted"}
    for r in con.execute(f"SELECT * FROM activity WHERE timestamp>=?{q} ORDER BY id DESC LIMIT 400", a):
        sens, ev, usr = r["sensitivity"], r["event_type"], r["username"]
        d = dict(id=f"A{r['id']}", ts=r["timestamp"], user=usr, file=r["file_path"],
                 detail=f"{sens} file" + (f", app: {r['application']}" if r["application"] else ""))
        if ev == "USB_INSERTED":
            out.append(dict(d, rule="R08", severity="LOW", title="USB device connected", detail=f"Drive {r['file_path']}"))
            continue
        if sens not in ("HIGH", "CRITICAL"):
            continue
        name = os.path.basename(r["file_path"]).lower()
        role = pol["assign"].get(usr)
        ok = bool(role) and name in [f.lower() for f in pol["roles"].get(role, [])]
        crit = sens == "CRITICAL"
        if ev == "MOVED":
            out.append(dict(d, rule="R05", severity="HIGH" if crit else "MEDIUM", title="Protected file moved or renamed",
                            detail=f"{sens} file, {r['application'] or 'new location unknown'}"))
        elif ev in ACT:
            act = ACT[ev]
            if ok and S["auto_approve"]:
                out.append(dict(d, rule="R06", severity="LOW", title=f"Permitted file {act}", permitted=True,
                                reason=f"The {role} role is allowed to use {name}. No alert is raised."))
            else:
                sv = ("CRITICAL" if crit else "HIGH") if act != "opened" else ("HIGH" if crit else "MEDIUM")
                who = f"The {role} role" if role else "This user (no role assigned)"
                out.append(dict(d, rule="R06", severity=sv, title=f"Unauthorised file {act}",
                                detail=f"{sens} file. {who} is not permitted to use {name}"))
    out.sort(key=lambda x: x["ts"]); kept, last = [], {}
    for x in out:                      # one alert per user, action and file within 30 s
        k, t = (x["user"], x["title"], x["file"]), datetime.fromisoformat(x["ts"])
        if k in last and (t - last[k]).total_seconds() < 30:
            continue
        last[k] = t; kept.append(x)
    out = kept
    ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    for x in out:                      # R07: out-of-hours escalation
        if x["rule"] != "R08" and not x.get("permitted") and not (WS <= datetime.fromisoformat(x["ts"]).hour < WE):
            x["severity"] = ORDER[min(ORDER.index(x["severity"]) + 1, 3)]
            x["esc"] = True; x["detail"] += " (outside working hours, severity raised)"
    states = {s["alert_id"]: s["status"] for s in con.execute("SELECT * FROM alert_state")}
    con.close()
    pol = load_policy()
    out = [x for x in out if x["rule"] not in pol["disabled_rules"]]
    for x in out:
        if x["id"] in states: x["status"], x["reason"] = states[x["id"]], x.get("reason", "")
        elif x.get("permitted"): x["status"] = "permitted"
        else: x["status"], x["reason"] = auto_decide(x, pol)
    if not permitted:
        out = [x for x in out if x["status"] != "permitted"]
    return sorted(out, key=lambda x: x["ts"], reverse=True)


@app.route("/")
def index():
    return send_from_directory(HERE, "dashboard.html")


@app.route("/api/users")
def users():
    m = int(request.args.get("window", 1440))
    con = db(); names = set()
    for t in ("activity", "transfers", "behavior_events"):
        names |= {r[0] for r in con.execute(f"SELECT DISTINCT username FROM {t}") if r[0]}
    res = []
    alerts = build_alerts(m)
    for n in sorted(names):
        mine_all = [a for a in alerts if a["user"] == n]
        s, lvl, b, raw = score_for(n, m, mine_all)
        last = max([x[0] for x in (con.execute(f"SELECT MAX(timestamp) FROM {t} WHERE username=?", (n,)).fetchone() for t in ("activity", "transfers", "behavior_events")) if x[0]] or [""])
        beh = con.execute("SELECT application,idle_seconds,timestamp FROM behavior_events WHERE username=? ORDER BY id DESC LIMIT 1", (n,)).fetchone()
        mine = [a for a in alerts if a["user"] == n and a["status"] == "open"]
        res.append(dict(name=n, role=load_policy()["assign"].get(n, "Unassigned"), device=platform.node(), score=s, raw=raw, flagged=any(a["status"] == "suspicious" for a in mine_all), level=lvl, behavior=b, last_seen=last,
                        open_alerts=len(mine), critical=sum(a["severity"] == "CRITICAL" for a in mine),
                        now=dict(beh) if beh else None))
    con.close()
    return jsonify(sorted(res, key=lambda u: -u["score"]))


@app.route("/api/alerts")
def alerts():
    a = build_alerts(int(request.args.get("window", 1440)), request.args.get("user"), request.args.get("permitted") == "1")
    st = request.args.get("status")
    return jsonify([x for x in a if not st or x["status"] == st])


@app.route("/api/alerts/<aid>", methods=["POST"])
def set_alert(aid):
    con = db()
    con.execute("INSERT OR REPLACE INTO alert_state VALUES (?,?,?)", (aid, request.json["status"], datetime.now().isoformat()))
    con.commit(); con.close()
    return jsonify(ok=True)


@app.route("/api/alerts.csv")
def alerts_csv():
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(["time", "user", "severity", "title", "file", "detail", "status"])
    for x in build_alerts(int(request.args.get("window", 1440))):
        w.writerow([x["ts"], x["user"], x["severity"], x["title"], x["file"], x["detail"], x["status"]])
    return Response(buf.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=dlp_alerts.csv"})


@app.route("/api/events")
def events():
    c = cutoff(int(request.args.get("window", 1440))); user = request.args.get("user"); cat = request.args.get("cat", "all")
    con = db(); q, a = " AND username=?" if user else "", ((c, user) if user else (c,))
    rows = [dict(r, kind="activity") for r in con.execute(f"SELECT * FROM activity WHERE timestamp>=?{q} ORDER BY id DESC LIMIT 150", a)]
    rows += [dict(r, kind="transfer") for r in con.execute(f"SELECT * FROM transfers WHERE timestamp>=?{q} ORDER BY id DESC LIMIT 150", a)]
    con.close()
    if cat in CATS:
        rows = [r for r in rows if r["event_type"] in CATS[cat]]
    return jsonify(sorted(rows, key=lambda e: e["timestamp"], reverse=True)[:80])


@app.route("/api/timeline")
def timeline():
    minutes = int(request.args.get("window", 1440)); user = request.args.get("user")
    step = max(1, minutes // 12); start = datetime.now() - timedelta(minutes=step * 12)
    bk = [dict(start=(start + timedelta(minutes=step * i)).isoformat(), activity=0, transfers=0) for i in range(12)]
    con = db(); q, a = " AND username=?" if user else "", ((start.isoformat(), user) if user else (start.isoformat(),))
    for t in ("activity", "transfers"):
        for r in con.execute(f"SELECT timestamp FROM {t} WHERE timestamp>=?{q}", a):
            i = int((datetime.fromisoformat(r[0]) - start).total_seconds() // (step * 60))
            if 0 <= i < 12: bk[i][t] += 1
    con.close()
    return jsonify(bk)


@app.route("/api/rules")
def rules():
    off = load_policy()["disabled_rules"]; hits = {}
    for a in build_alerts(30 * 1440):
        hits[a["rule"]] = hits.get(a["rule"], 0) + 1
        if a.get("esc"): hits["R07"] = hits.get("R07", 0) + 1
    return jsonify([dict(id=r[0], name=r[1], source=r[2], severity=r[3], iso=r[4], why=r[5], enabled=r[0] not in off, hits=hits.get(r[0], 0)) for r in RULES])


@app.route("/api/rules/<rid>", methods=["POST"])
def toggle_rule(rid):
    pol = load_policy()
    if rid in pol["disabled_rules"]: pol["disabled_rules"].remove(rid)
    else: pol["disabled_rules"].append(rid)
    save_policy(pol)
    return jsonify(ok=True)


@app.route("/api/settings", methods=["GET", "POST"])
def settings():
    pol = load_policy()
    if request.method == "POST":
        for k, v in request.json.items():
            if k in pol["settings"]:
                pol["settings"][k] = bool(v) if k == "auto_approve" else max(1, int(v))
        save_policy(pol)
    return jsonify(pol["settings"])


@app.route("/api/roles")
def roles():
    pol = load_policy(); con = db(); names = set()
    for t in ("activity", "transfers", "behavior_events"):
        names |= {r[0] for r in con.execute(f"SELECT DISTINCT username FROM {t}") if r[0]}
    con.close()
    return jsonify(roles=pol["roles"], assign=pol["assign"], users=sorted(names | set(pol["assign"])))


@app.route("/api/roles/assign", methods=["POST"])
def assign_role():
    pol = load_policy(); d = request.json
    if d["role"] == "Unassigned": pol["assign"].pop(d["user"], None)
    else: pol["assign"][d["user"]] = d["role"]
    save_policy(pol)
    return jsonify(ok=True)


@app.route("/api/policies")
def policies():
    m = 1440 * 30; con = db(); files = []
    for p, sens in SENSITIVE_FILES.items():
        n = os.path.basename(p)
        acc = con.execute("SELECT COUNT(*) FROM activity WHERE file_path LIKE ?", ("%" + n,)).fetchone()[0]
        tr = con.execute("SELECT COUNT(*) FROM transfers WHERE source_path LIKE ?", ("%" + n.lower(),)).fetchone()[0]
        files.append(dict(name=n, path=p, sensitivity=sens, exists=os.path.isfile(p), accesses=acc, transfers=tr))
    con.close()
    return jsonify(files=files)


LOGDIR = os.path.join(HERE, "data", "logs")


def start(key):
    os.makedirs(LOGDIR, exist_ok=True)
    return subprocess.Popen([sys.executable, "-u", os.path.join(HERE, MONITORS[key][0])], cwd=HERE,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        stdout=open(os.path.join(LOGDIR, key + ".log"), "w"), stderr=subprocess.STDOUT)


def tail(key):
    try: return open(os.path.join(LOGDIR, key + ".log")).read()[-300:].strip()
    except OSError: return ""


@app.route("/api/monitors")
def monitors():
    out = []
    for k, v in MONITORS.items():
        pr = procs.get(k); running = bool(pr and pr.poll() is None); ex = bool(pr and not running)
        out.append(dict(key=k, script=v[0], name=v[1], desc=v[2], running=running, exited=ex, log=tail(k) if ex else ""))
    return jsonify(out)


@app.route("/api/monitors/<key>", methods=["POST"])
def toggle(key):
    p = procs.get(key)
    if p and p.poll() is None: p.terminate()
    elif key in MONITORS:
        procs[key] = start(key)
    return monitors()


@app.route("/api/reset", methods=["POST"])
def reset():
    con = db()
    for t in ("activity", "transfers", "behavior_events", "alert_state"): con.execute(f"DELETE FROM {t}")
    con.commit(); con.close()
    return jsonify(ok=True)


if __name__ == "__main__":
    os.chdir(HERE); os.makedirs("data", exist_ok=True); ensure_tables()
    print("DataShield: http://127.0.0.1:8000")
    try: app.run(host="127.0.0.1", port=8000, debug=False)
    finally:
        for p in procs.values():
            if p.poll() is None: p.terminate()