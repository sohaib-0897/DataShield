"""Isolated baseline for the existing DataShield source; never run monitor main().

Run with python3 -B tests/phase0_regression.py --source-root /path/to/source.
An optional --dependency-root adds an existing site-packages directory for Flask.
Missing dependencies are recorded as skips, never silently counted as verification.
"""
import argparse
import ast
import contextlib
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import types
import unittest
from datetime import datetime
from unittest.mock import patch

SOURCE = None
FLASK_ERROR = None
PANDAS_ERROR = None


class Clock(datetime):
    @classmethod
    def now(cls, tz=None):
        value = cls(2026, 10, 7, 12)
        return value if tz is None else value.replace(tzinfo=tz)


class Baseline(unittest.TestCase):
    def setUp(self):
        self.sandbox = tempfile.TemporaryDirectory(prefix="datashield-phase0-")
        self.addCleanup(self.sandbox.cleanup)
        self.root = Path(self.sandbox.name).resolve()
        old_cwd = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, old_cwd)
        connect = sqlite3.connect

        def isolated_connect(database, *args, **kwargs):
            if str(database) != ":memory:":
                target = Path(database).resolve()
                if not target.is_relative_to(self.root):
                    raise AssertionError(f"SQLite outside temporary sandbox: {target}")
            return connect(database, *args, **kwargs)

        self.enterContext(patch("sqlite3.connect", side_effect=isolated_connect))
        self.enterContext(patch.object(subprocess, "Popen", side_effect=AssertionError("No processes permitted")))
        self.database = importlib.import_module("database")
        self.behavior = importlib.import_module("behavior")
        self.risk = importlib.import_module("risk_engine")
        self.sensitivity = importlib.import_module("sensitivity")
        self.path = self.root / "data" / "activity.db"
        for module in (self.database, self.behavior):
            self.enterContext(patch.object(module, "DB_PATH", str(self.path)))
            self.enterContext(patch.object(module, "datetime", Clock))
        self.database.initialize_database()
        self.database.initialize_transfer_table()

    def console(self):
        if FLASK_ERROR:
            self.skipTest(f"Flask unavailable: {FLASK_ERROR}")
        module = importlib.import_module("dashboard")
        for key, value in {
            "DB_PATH": str(self.path), "POLICY_PATH": str(self.root / "data" / "policy.json"),
            "LOGDIR": str(self.root / "data" / "logs"), "datetime": Clock, "procs": {},
        }.items():
            self.enterContext(patch.object(module, key, value))
        self.enterContext(patch.object(module, "SENSITIVE_FILES", {str(self.root / "salary.xlsx"): "HIGH"}))
        module.ensure_tables()
        module.app.config["TESTING"] = True
        return module, module.app.test_client()

    def activity(self, user="alice", event="FILE_READ", path="salary.xlsx", sensitivity="HIGH", ts="2026-10-07T10:00:00"):
        with sqlite3.connect(self.path) as con:
            con.execute("INSERT INTO activity(timestamp,username,event_type,file_path,sensitivity,application) VALUES(?,?,?,?,?,?)",
                        (ts, user, event, path, sensitivity, "excel.exe"))

    def transfer(self, user="alice", event="SENSITIVE_USB_COPY"):
        with sqlite3.connect(self.path) as con:
            con.execute("INSERT INTO transfers(timestamp,username,event_type,source_path,destination_path,sensitivity,destination_type,file_hash) VALUES(?,?,?,?,?,?,?,?)",
                        ("2026-10-07T10:00:00", user, event, "salary.xlsx", "E:/salary.xlsx", "HIGH", "USB", "synthetic-hash"))

    def test_schema_and_append_logging(self):
        with patch("getpass.getuser", return_value="synthetic-user"):
            self.database.log_activity("FILE_READ", "salary.xlsx", "HIGH", "excel.exe")
            self.database.log_transfer("SENSITIVE_USB_COPY", "salary.xlsx", "E:/salary.xlsx", "HIGH", "USB", "hash")
        self.database.initialize_database()
        self.database.initialize_transfer_table()
        with sqlite3.connect(self.path) as con:
            self.assertEqual(con.execute("SELECT username,event_type,application FROM activity").fetchall(),
                             [("synthetic-user", "FILE_READ", "excel.exe")])
            self.assertEqual(con.execute("SELECT username,file_hash FROM transfers").fetchall(), [("synthetic-user", "hash")])
            self.assertEqual([r[1] for r in con.execute("PRAGMA table_info(activity)")],
                             ["id", "timestamp", "username", "event_type", "file_path", "sensitivity", "application"])

    def test_empty_behavior_and_risk(self):
        b = self.behavior.get_behavior("nobody", 1440)
        self.assertTrue(all(v == 0 for k, v in b.items() if k != "window_minutes"))
        self.assertEqual(self.risk.calculate_risk("nobody")["risk_level"], "LOW")

    def test_behavior_user_isolation_and_counts(self):
        self.activity()
        self.activity(event="FILE_WRITE")
        self.activity(user="bob", sensitivity="CRITICAL")
        self.transfer()
        b = self.behavior.get_behavior("alice", 1440)
        self.assertEqual((b["total_activity_events"], b["repeated_accesses"], b["files_modified"], b["usb_copies"]), (2, 1, 1, 1))
        self.assertEqual(b["critical_files_accessed"], 0)
        self.assertEqual(self.behavior.get_behavior("' OR 1=1 --", 1440)["total_activity_events"], 0)

    def test_rule_score_caps_and_boundaries(self):
        b = {k: 100 for k in ("sensitive_files_accessed", "repeated_accesses", "critical_files_accessed", "files_modified", "after_hours_events")}
        self.assertEqual(self.risk.calculate_dlp_score(b), 85)
        self.assertEqual([self.risk.get_risk_level(s) for s in (0, 24, 25, 49, 50, 74, 75, 100)],
                         ["LOW", "LOW", "MEDIUM", "MEDIUM", "HIGH", "HIGH", "CRITICAL", "CRITICAL"])

    def test_filename_and_hash_signals(self):
        fixture = self.root / "salary.xlsx"
        fixture.write_bytes(b"synthetic test fixture")
        with patch.object(self.sensitivity, "SENSITIVE_FILES", {str(fixture): "HIGH"}):
            self.assertEqual(self.sensitivity.get_sensitivity(str(self.root / "SALARY.XLSX")), "HIGH")
            self.assertEqual(self.sensitivity.get_sensitivity("unknown.txt"), "NORMAL")
            digest = hashlib.sha256(fixture.read_bytes()).hexdigest()
            self.assertEqual(self.sensitivity.calculate_hash(fixture), digest)
            self.assertEqual(self.sensitivity.build_sensitive_hashes()[digest]["sensitivity"], "HIGH")
            self.assertIsNone(self.sensitivity.calculate_hash(self.root / "missing"))

    def test_dashboard_empty_api_contracts(self):
        _, client = self.console()
        for route in ("/api/users", "/api/alerts", "/api/events"):
            response = client.get(route)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), [])
        self.assertEqual(client.get("/").status_code, 200)
        self.assertEqual(len(client.get("/api/timeline").get_json()), 12)
        self.assertEqual(set(client.get("/api/roles").get_json()), {"roles", "assign", "users"})
        self.assertEqual(set(client.get("/api/policies").get_json()), {"files"})
        self.assertEqual(len(client.get("/api/rules").get_json()), 8)
        self.assertEqual(len(client.get("/api/monitors").get_json()), 7)

    def test_dashboard_event_alert_and_user_fields(self):
        _, client = self.console()
        self.activity()
        self.transfer()
        alerts = client.get("/api/alerts?window=1440").get_json()
        self.assertEqual({x["rule"] for x in alerts}, {"R01", "R06"})
        self.assertTrue({"id", "ts", "user", "severity", "title", "file", "detail", "rule", "status", "reason"} <= set(alerts[0]))
        users = client.get("/api/users?window=1440").get_json()
        self.assertTrue({"name", "role", "device", "score", "raw", "flagged", "level", "behavior", "last_seen", "open_alerts", "critical", "now"} <= set(users[0]))
        events = client.get("/api/events?cat=usb&user=alice").get_json()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["kind"], "transfer")
        self.assertEqual(client.get("/api/events?user=bob").get_json(), [])
        self.assertEqual(client.get("/api/timeline?window=1440&user=alice").get_json()[11]["transfers"], 1)
        response = client.get("/api/alerts.csv")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.startswith(b"time,user,severity,title,file,detail,status"))

    def test_role_policy_persistence_and_external_alerts(self):
        module, client = self.console()
        self.activity()
        self.transfer()
        self.assertEqual(client.post("/api/roles/assign", json={"user": "alice", "role": "Finance"}).get_json(), {"ok": True})
        self.assertEqual(json.loads(Path(module.POLICY_PATH).read_text())["assign"]["alice"], "Finance")
        self.assertEqual({a["rule"] for a in client.get("/api/alerts").get_json()}, {"R01"})
        permitted = client.get("/api/alerts?permitted=1").get_json()
        self.assertIn("permitted", {a["status"] for a in permitted})
        client.post("/api/roles/assign", json={"user": "alice", "role": "Unassigned"})
        self.assertNotIn("alice", module.load_policy()["assign"])

    def test_settings_rule_toggle_and_policy_preservation(self):
        module, client = self.console()
        self.transfer()
        pol = module.load_policy()
        pol["custom_extension"] = {"preserve": True}
        module.save_policy(pol)
        response = client.post("/api/settings", json={"half_life_h": 12, "auto_approve": False, "unknown": 42})
        self.assertEqual(response.get_json()["half_life_h"], 12)
        self.assertFalse(response.get_json()["auto_approve"])
        self.assertNotIn("unknown", response.get_json())
        self.assertTrue(module.load_policy()["custom_extension"]["preserve"])
        client.post("/api/rules/R01")
        self.assertEqual(client.get("/api/alerts").get_json(), [])
        client.post("/api/rules/R01")
        self.assertEqual(len(client.get("/api/alerts").get_json()), 1)

    def test_analyst_decisions_persist_and_change_risk(self):
        module, client = self.console()
        self.transfer()
        aid = client.get("/api/alerts").get_json()[0]["id"]
        original = client.get("/api/users").get_json()[0]["score"]
        self.assertGreater(original, 0)
        client.post(f"/api/alerts/{aid}", json={"status": "approved"})
        self.assertEqual(client.get("/api/users").get_json()[0]["score"], 0)
        client.post(f"/api/alerts/{aid}", json={"status": "suspicious"})
        user = client.get("/api/users").get_json()[0]
        self.assertTrue(user["flagged"])
        self.assertGreaterEqual(user["score"], module.load_policy()["settings"]["flag_floor"])
        with sqlite3.connect(self.path) as con:
            self.assertEqual(con.execute("SELECT status FROM alert_state WHERE alert_id=?", (aid,)).fetchone()[0], "suspicious")
        client.post(f"/api/alerts/{aid}", json={"status": "open"})
        self.assertEqual(client.get("/api/users").get_json()[0]["score"], original)

    def test_alert_deduplication_after_hours_and_usb_autoapproval(self):
        _, client = self.console()
        self.activity(ts="2026-10-07T08:00:00")
        self.activity(ts="2026-10-07T08:00:10")
        self.activity(event="USB_INSERTED", path="E:", sensitivity="NORMAL")
        alerts = client.get("/api/alerts").get_json()
        self.assertEqual(len(alerts), 2)
        access = next(a for a in alerts if a["rule"] == "R06")
        self.assertTrue(access["esc"])
        self.assertEqual(access["severity"], "HIGH")
        self.assertEqual(next(a for a in alerts if a["rule"] == "R08")["status"], "auto_approved")

    def test_monitor_controls_use_fake_processes(self):
        module, client = self.console()
        process = unittest.mock.Mock()
        process.poll.return_value = None
        with patch.object(module, "start", return_value=process) as start:
            self.assertEqual(client.post("/api/monitors/files").status_code, 200)
            start.assert_called_once_with("files")
            self.assertTrue(next(m for m in client.get("/api/monitors").get_json() if m["key"] == "files")["running"])
            client.post("/api/monitors/files")
            process.terminate.assert_called_once()

    def test_upload_hash_detection_logs_only_known_content(self):
        if FLASK_ERROR:
            self.skipTest(f"Flask unavailable: {FLASK_ERROR}")
        with patch.object(self.sensitivity, "build_sensitive_hashes", return_value={}):
            module = importlib.import_module("upload_server")
        digest = hashlib.sha256(b"synthetic protected text").hexdigest()
        self.enterContext(patch.object(module, "UPLOAD_FOLDER", str(self.root)))
        self.enterContext(patch.object(module, "SENSITIVE_HASHES", {digest: {"source_path": "synthetic.txt", "sensitivity": "HIGH"}}))
        client = module.app.test_client()
        self.assertEqual(client.post("/upload").status_code, 400)
        with contextlib.redirect_stdout(io.StringIO()):
            response = client.post("/upload", data={"file": (io.BytesIO(b"synthetic protected text"), "renamed.txt")})
            self.assertEqual(response.status_code, 200)
            client.post("/upload", data={"file": (io.BytesIO(b"ordinary synthetic fixture"), "ordinary.txt")})
        with sqlite3.connect(self.path) as con:
            self.assertEqual(con.execute("SELECT event_type,file_hash FROM transfers").fetchall(), [("SENSITIVE_UPLOAD", digest)])

    def test_copy_handlers_without_observers_or_devices(self):
        content = b"synthetic copy fixture"
        copied = self.root / "renamed.txt"
        copied.write_bytes(content)
        normal = self.root / "normal.txt"
        normal.write_bytes(b"ordinary fixture")
        digest = hashlib.sha256(content).hexdigest()
        specs = (("local_copy_monitor", "LocalCopyHandler", "SENSITIVE_LOCAL_COPY"),
                 ("usb_copy_monitor", "USBFileHandler", "SENSITIVE_USB_COPY"),
                 ("google_drive_monitor", "GoogleDriveHandler", "SENSITIVE_CLOUD_COPY"))
        for name, handler, event in specs:
            with self.subTest(channel=name):
                module = importlib.import_module(name)
                with patch.object(module, "SENSITIVE_HASHES", {digest: {"source_path": "synthetic.txt", "sensitivity": "HIGH"}}), \
                     patch.object(module, "Observer", side_effect=AssertionError("No observers permitted")), \
                     patch.object(module.time, "sleep"), contextlib.redirect_stdout(io.StringIO()):
                    instance = getattr(module, handler)()
                    instance.check_file(str(copied))
                    instance.check_file(str(normal))
                with sqlite3.connect(self.path) as con:
                    self.assertEqual(con.execute("SELECT file_hash FROM transfers WHERE event_type=?", (event,)).fetchall(), [(digest,)])

    def test_preexisting_permitted_after_hours_characterization(self):
        # Current behavior is recorded, not endorsed: role-permitted access stays hidden after hours.
        _, client = self.console()
        self.activity(ts="2026-10-07T08:00:00")
        client.post("/api/roles/assign", json={"user": "alice", "role": "Finance"})
        self.assertEqual(client.get("/api/alerts").get_json(), [])
        event = client.get("/api/alerts?permitted=1").get_json()[0]
        self.assertEqual(event["status"], "permitted")
        self.assertNotIn("esc", event)

    def test_windows_xml_and_access_parser_mock_only(self):
        # No EvtSubscribe, native Security log, devices, or monitoring loop is invoked.
        with patch.dict(sys.modules, {"win32evtlog": types.ModuleType("win32evtlog")}):
            module = importlib.import_module("windows_monitor")
        xml = '<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event"><System><EventID>4663</EventID></System><EventData><Data Name="AccessList">%%4416</Data></EventData></Event>'
        self.assertEqual(module.get_event_data(xml), ("4663", {"AccessList": "%%4416"}))
        self.assertEqual(module.classify_access("%%4416"), "READ")
        self.assertEqual(module.classify_access("%%4416 %%4417"), "WRITE")
        self.assertEqual(module.classify_access("%%4416 %%1537"), "DELETE")
        self.assertIsNone(module.classify_access(""))

    def test_behavior_telemetry_logging_mock_only(self):
        with patch.dict(sys.modules, {name: types.ModuleType(name) for name in ("win32gui", "win32process")}):
            module = importlib.import_module("behavioral_monitor")
        self.enterContext(patch.object(module, "DB_PATH", str(self.path)))
        module.initialize_behavior_table()
        module.log_behavior("USER_IDLE", "synthetic.exe", "synthetic title", 65)
        with sqlite3.connect(self.path) as con:
            self.assertEqual(con.execute("SELECT event_type,application,idle_seconds FROM behavior_events").fetchall(), [("USER_IDLE", "synthetic.exe", 65)])

    def features(self):
        if PANDAS_ERROR:
            self.skipTest(f"pandas unavailable: {PANDAS_ERROR}")
        module = importlib.import_module("feature_builder")
        self.enterContext(patch.object(module, "DB_PATH", str(self.path)))
        return module

    def test_feature_both_sources_empty(self):
        module = self.features()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(module.build_features().empty)

    def test_feature_activity_only(self):
        module = self.features()
        self.activity()
        self.assertEqual(int(module.build_features()["total_activity_events"].sum()), 1)

    def test_feature_transfer_only(self):
        module = self.features()
        self.transfer()
        self.assertEqual(int(module.build_features()["total_transfer_events"].sum()), 1)

    def test_feature_existing_global_aggregation_characterization(self):
        module = self.features()
        self.activity()
        self.activity(user="bob")
        self.transfer()
        df = module.build_features()
        self.assertEqual(len(df), 1)
        self.assertNotIn("username", df.columns)
        self.assertEqual(int(df.iloc[0]["total_activity_events"]), 2)

    def test_existing_source_syntax_without_import_side_effects(self):
        paths = sorted(SOURCE.glob("*.py"))
        self.assertGreaterEqual(len(paths), 18)
        for path in paths:
            with self.subTest(file=path.name):
                ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))


def main():
    global SOURCE, FLASK_ERROR, PANDAS_ERROR
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--dependency-root", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--test", action="append", help="Run only this named Baseline test; repeat for multiple tests")
    parser.add_argument("--require-no-skips", action="store_true", help="Exit nonzero if any selected check is skipped")
    args = parser.parse_args()
    SOURCE = args.source_root.resolve()
    if not all((SOURCE / name).is_file() for name in ("database.py", "dashboard.py", "dashboard.html", "feature_builder.py")):
        parser.error("source root must contain the existing DataShield application")
    if args.test:
        for name in args.test:
            if not name.startswith("test_") or not callable(getattr(Baseline, name, None)):
                parser.error(f"Unknown baseline test: {name}")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(SOURCE))
    if args.dependency_root:
        sys.path.append(str(args.dependency_root.resolve()))
    for name in ("flask", "pandas"):
        try:
            importlib.import_module(name)
        except Exception as exc:
            error = f"{type(exc).__name__}: {str(exc).splitlines()[0]}"
            if name == "flask":
                FLASK_ERROR = error
            else:
                PANDAS_ERROR = error
    suite = (unittest.TestSuite(Baseline(name) for name in args.test) if args.test
             else unittest.defaultTestLoader.loadTestsFromTestCase(Baseline))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"source_root": str(SOURCE), "dependency_root": str(args.dependency_root) if args.dependency_root else None,
              "python": sys.version.split()[0], "run": result.testsRun,
              "passed": result.testsRun - len(result.skipped) - len(result.failures) - len(result.errors),
              "skipped": [{"test": str(test), "reason": reason} for test, reason in result.skipped],
              "failures": [{"test": str(test), "traceback": trace} for test, trace in result.failures],
              "errors": [{"test": str(test), "traceback": trace} for test, trace in result.errors],
              "flask_import_error": FLASK_ERROR, "pandas_import_error": PANDAS_ERROR,
              "native_windows_verified": False, "monitors_started": False,
              "fixture_data": "synthetic; temporary SQLite and policy files", "successful_available_checks": result.wasSuccessful(),
              "selected_tests": args.test, "complete_verification": result.wasSuccessful() and not result.skipped}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    if not result.wasSuccessful():
        return 1
    return 2 if args.require_no_skips and result.skipped else 0


if __name__ == "__main__":
    raise SystemExit(main())
