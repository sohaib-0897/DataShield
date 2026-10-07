"""Isolated, bounded CERT research ingestion; never imports application code.

Raw content stays in ignored research/local. No answers or labels enter events.
"""
from __future__ import annotations

import argparse
import bz2
import csv
from contextlib import closing
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import tarfile
import time

VERSION = "cert-r42-ingestion-v1"
MAX_FIELD = 8 * 1024 * 1024
MAX_RECORD = 16 * 1024 * 1024
DEFAULT_RESERVE = 256 * 1024 * 1024


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def log_progress(value):
    print(value, flush=True)


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(encoded(value) + "\n", encoding="utf-8")
    temporary.replace(path)


def stat_identity(path):
    stat = path.stat()
    return (stat.st_size, stat.st_mtime_ns, stat.st_ino)


def hash_file(path):
    before = stat_identity(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    if stat_identity(path) != before:
        raise ValueError("Input changed while hashing")
    return {"sha256": digest.hexdigest(), "bytes": before[0]}


def require_space(folder, requested=0, reserve=DEFAULT_RESERVE):
    if requested < 0 or reserve < 0:
        raise ValueError("Disk bounds must be nonnegative")
    if shutil.disk_usage(folder).free < reserve + requested:
        raise OSError("Insufficient disk space for bounded research output")


def local_path(folder, candidate):
    """Reject lexical escape and symlinks, including symlinked ancestors."""
    folder = Path(folder).absolute()
    candidate = Path(candidate).absolute()
    if ".." in candidate.parts or not candidate.is_relative_to(folder):
        raise ValueError("Research output must stay inside research/local")
    for parent in (candidate, *candidate.parents):
        if parent.is_symlink():
            raise ValueError("Symlinked research destinations are forbidden")
    return candidate


def safe_member(member, seen):
    name = member.name
    parts = PurePosixPath(name).parts
    if not parts or name.startswith("/") or "\\" in name or ".." in parts or any(":" in p for p in parts):
        raise ValueError("Unsafe archive member path")
    canonical = str(PurePosixPath(name))
    if canonical in seen:
        raise ValueError("Duplicate archive member path")
    seen.add(canonical)
    if member.size < 0 or not (member.isdir() or member.isfile()):
        raise ValueError("Archive links and special files are forbidden")
    return canonical


class RecordLines:
    """Bound each logical CSV record even when quoted fields span lines."""
    def __init__(self, stream):
        self.stream = stream
        self.used = 0

    def __iter__(self):
        return self

    def __next__(self):
        line = self.stream.readline(MAX_RECORD + 1)
        if not line:
            raise StopIteration
        self.used += len(line.encode("utf-8"))
        if self.used > MAX_RECORD:
            raise ValueError("Oversized CSV record")
        return line

    def reset(self):
        self.used = 0


class ForwardMember(io.RawIOBase):
    """Expose a tar stream as a forward-only readable object to TextIOWrapper."""
    def __init__(self, stream):
        self.stream = stream

    def readable(self):
        return True

    def readinto(self, buffer):
        data = self.stream.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)

    def close(self):
        self.stream.close()
        super().close()


def inspect_archive(archive_path, folder, *, rows=1000, max_expanded=32 * 1024**3,
                    max_cache=128 * 1024**2, max_metadata=16 * 1024**2,
                    reserve=DEFAULT_RESERVE, progress=log_progress):
    """Validate every member, retain bounded CSV prefixes; publish only after EOF.

    No tar paths are used as filesystem output paths. Failed scans cannot publish
    a trusted manifest. Prefix caches use numbered files inside a unique staging
    directory; completed manifests and caches are content hashed.
    """
    if rows < 1 or max_cache < 1 or max_expanded < 1 or max_metadata < 1:
        raise ValueError("Inspection bounds must be positive")
    folder = local_path(folder, folder)
    folder.mkdir(parents=True, exist_ok=True)
    require_space(folder, max_cache, reserve)
    before = stat_identity(archive_path)
    fingerprint = hash_file(archive_path)
    import tempfile
    staging = Path(tempfile.mkdtemp(prefix="scan-", dir=folder))
    seen, members, expanded, cached, metadata_bytes = set(), [], 0, 0, 0
    started = time.monotonic()
    csv.field_size_limit(MAX_FIELD)
    # BZ2File handles the concatenated bzip2 streams present in the supplied r4.2.
    with bz2.BZ2File(archive_path, "rb") as source, tarfile.open(fileobj=source, mode="r|") as archive:
        for member in archive:
            if len(members) >= 100000:
                raise ValueError("Archive exceeds member-count budget")
            name = safe_member(member, seen)
            expanded += member.size
            if expanded > max_expanded:
                raise ValueError("Archive exceeds expanded-size budget")
            record = {"name": name, "bytes": member.size, "type": "file" if member.isfile() else "directory"}
            if member.isfile() and name.lower().endswith(".csv"):
                target = staging / f"rows-{len(members):05d}.jsonl"
                raw = io.BufferedReader(ForwardMember(archive.extractfile(member)))
                with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as text:
                    lines = RecordLines(text)
                    reader = csv.reader(lines, strict=True)
                    header = next(reader, [])
                    lines.reset()
                    record["header"] = header
                    count, eof = 0, False
                    with target.open("x", encoding="utf-8") as output:
                        for index in range(rows + 1):
                            values = next(reader, None)
                            lines.reset()
                            if values is None:
                                eof = True
                                break
                            if index == rows:
                                break
                            line = encoded(values) + "\n"
                            size = len(line.encode("utf-8"))
                            cached += size
                            if cached > max_cache:
                                raise ValueError("CSV prefixes exceed cache budget")
                            require_space(folder, size, reserve)
                            output.write(line)
                            count += 1
                record.update(cache=str(target.relative_to(folder)), cache_hash=hash_file(target)["sha256"],
                              cached_rows=count, complete=eof)
            elif member.isfile() and "readme" in name.lower():
                if member.size > 1024 * 1024:
                    raise ValueError("Oversized release README")
                record["release_document"] = archive.extractfile(member).read().decode("utf-8-sig")
            metadata_bytes += len(encoded(record).encode("utf-8"))
            if metadata_bytes > max_metadata:
                raise ValueError("Archive metadata exceeds memory budget")
            members.append(record)
            if progress:
                progress(encoded({"member": name, "expanded_bytes": expanded, "cached_bytes": cached,
                                  "elapsed_seconds": round(time.monotonic() - started, 1)}))
        # Consume trailing compression bytes too, surfacing CRC/truncation errors.
        while source.read(1024 * 1024):
            pass
    if stat_identity(archive_path) != before:
        raise ValueError("Archive changed during inspection")
    result = {"version": VERSION, "archive": archive_path.name, "input": fingerprint,
              "row_bound_per_member": rows, "members": members, "expanded_bytes": expanded,
              "cached_bytes": cached, "all_members_validated": True,
              "elapsed_seconds": round(time.monotonic() - started, 3)}
    result["manifest_sha256"] = hashlib.sha256(encoded(result).encode()).hexdigest()
    manifest = staging / "manifest.json"
    atomic_json(manifest, result)
    return manifest


# Established from the supplied r4.2/readme.txt and actual CSV headers.
# Columns/actions are preserved verbatim; action defaults below are documented
# release semantics for sources that have no activity column.
SOURCES = {
    "file.csv": {"header": ["id", "date", "user", "pc", "filename", "content"],
                 "channel": "FILE", "action": "copy_to_removable_media", "resource": "filename"},
    "http.csv": {"header": ["id", "date", "user", "pc", "url", "content"],
                 "channel": "HTTP", "action": "visit", "resource": "url"},
    "logon.csv": {"header": ["id", "date", "user", "pc", "activity"],
                  "channel": "LOGON", "action": None, "actions": {"logon", "logoff"}, "resource": None},
    "device.csv": {"header": ["id", "date", "user", "pc", "activity"],
                   "channel": "USB", "action": None, "actions": {"connect", "disconnect"}, "resource": None},
    "email.csv": {"header": ["id", "date", "user", "pc", "to", "cc", "bcc", "from", "size", "attachments", "content"],
                  "channel": "EMAIL", "action": "send", "resource": "to"},
}


def normalize(filename, header, values):
    if not values:
        raise ValueError("empty_row")
    if len(values) != len(header):
        raise ValueError("field_count")
    row = dict(zip(header, values))
    for name in ("id", "date", "user", "pc"):
        if not row.get(name, "").strip():
            raise ValueError("missing_" + name)
    try:
        timestamp = datetime.strptime(row["date"], "%m/%d/%Y %H:%M:%S").isoformat()
    except ValueError:
        raise ValueError("invalid_timestamp") from None
    specification = SOURCES[filename]
    action = row.get("activity", specification["action"])
    if not action or (specification.get("actions") and action.casefold() not in specification["actions"]):
        raise ValueError("unsupported_action")
    resource = row.get(specification["resource"]) if specification["resource"] else None
    if specification["resource"] and not resource:
        raise ValueError("missing_resource")
    return {"source_id": row["id"], "user": row["user"], "pc": row["pc"], "timestamp_raw": row["date"],
            "timestamp_local": timestamp, "channel": specification["channel"], "action": action,
            "resource": resource, "metadata_json": encoded(row),
            "row_hash": hashlib.sha256(encoded(row).encode()).hexdigest()}


SCHEMA = """
CREATE TABLE IF NOT EXISTS datasets (
 sha256 TEXT PRIMARY KEY, version TEXT NOT NULL, manifest_sha256 TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events (
 dataset_sha256 TEXT NOT NULL REFERENCES datasets(sha256), source_file TEXT NOT NULL,
 source_id TEXT NOT NULL, source_row INTEGER NOT NULL, username TEXT NOT NULL, pc TEXT NOT NULL,
 timestamp_raw TEXT NOT NULL, timestamp_local TEXT NOT NULL, timezone_basis TEXT NOT NULL,
 channel TEXT NOT NULL, action TEXT NOT NULL, resource TEXT, metadata_json TEXT NOT NULL,
 row_hash TEXT NOT NULL, PRIMARY KEY(dataset_sha256,source_file,source_id));
CREATE INDEX IF NOT EXISTS events_user_time ON events(username,timestamp_local);
CREATE TABLE IF NOT EXISTS diagnostics (
 dataset_sha256 TEXT NOT NULL, source_file TEXT NOT NULL, source_row INTEGER NOT NULL,
 reason TEXT NOT NULL, PRIMARY KEY(dataset_sha256,source_file,source_row));
CREATE TABLE IF NOT EXISTS progress (
 dataset_sha256 TEXT NOT NULL, source_file TEXT NOT NULL, cache_hash TEXT NOT NULL,
 processed INTEGER NOT NULL, valid INTEGER NOT NULL, inserted INTEGER NOT NULL,
 duplicates INTEGER NOT NULL, invalid INTEGER NOT NULL,
 PRIMARY KEY(dataset_sha256,source_file));
"""


def verified_manifest(manifest, folder):
    manifest = local_path(folder, manifest)
    result = json.loads(manifest.read_text())
    expected = result.pop("manifest_sha256")
    if hashlib.sha256(encoded(result).encode()).hexdigest() != expected:
        raise ValueError("Inspection manifest changed")
    result["manifest_sha256"] = expected
    if result.get("version") != VERSION or not result.get("all_members_validated"):
        raise ValueError("Unvalidated or incompatible inspection")
    seen = set()
    for member in result["members"]:
        if member["name"] in seen:
            raise ValueError("Duplicate member in manifest")
        seen.add(member["name"])
        if "cache" in member:
            cache = local_path(folder, folder / member["cache"])
            if hash_file(cache)["sha256"] != member["cache_hash"]:
                raise ValueError("CSV prefix changed")
    return result


def ingest(manifest, folder, database, *, chunk=500, limit=None, reserve=DEFAULT_RESERVE,
           after_chunk=None, progress_log=log_progress):
    """Serialize writers using a separate SQLite lock released on crash/exit."""
    database = local_path(folder, database)
    guard_path = local_path(folder, database.with_suffix(database.suffix + ".writer-lock.sqlite"))
    require_space(folder, reserve=reserve)
    database.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(guard_path, timeout=0)) as guard:
        try:
            guard.execute("BEGIN EXCLUSIVE")
        except sqlite3.OperationalError:
            raise RuntimeError("Another research ingestion writer is active") from None
        try:
            return _ingest(manifest, folder, database, chunk=chunk, limit=limit, reserve=reserve,
                           after_chunk=after_chunk, progress_log=progress_log)
        finally:
            guard.rollback()


def _ingest(manifest, folder, database, *, chunk=500, limit=None, reserve=DEFAULT_RESERVE,
            after_chunk=None, progress_log=log_progress):
    """Resume committed CSV record positions; commits include counters and diagnostics.

    limit is an absolute per-file row bound. Increasing it resumes existing caches;
    re-running the same bound processes no rows. Dataset identity and source event
    ID deduplication also protect replays from independently prepared prefixes.
    """
    if chunk < 1 or (limit is not None and limit < 1):
        raise ValueError("Row/chunk bounds must be positive")
    database = local_path(folder, database)
    result = verified_manifest(manifest, folder)
    dataset = result["input"]["sha256"]
    selected = [m for m in result["members"] if PurePosixPath(m["name"]).name in SOURCES
                and m["name"].startswith("r4.2/") and len(PurePosixPath(m["name"]).parts) == 2]
    found = {PurePosixPath(m["name"]).name for m in selected}
    if found != set(SOURCES):
        raise ValueError("Missing release event sources")
    for member in selected:
        filename = PurePosixPath(member["name"]).name
        if member.get("cache_format") not in (None, "indexed-v1"):
            raise ValueError("Unsupported cache format")
        if member["header"] != SOURCES[filename]["header"]:
            raise ValueError("Unsupported release header")
        if limit and limit > member["cached_rows"] and not member["complete"]:
            raise ValueError("Requested row limit exceeds prepared prefix")
    database.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database)) as db, db:
        application_id = db.execute("PRAGMA application_id").fetchone()[0]
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        if application_id not in (0, 0x43455254) or (application_id == 0 and tables):
            raise ValueError("Existing database is not a CERT research store")
        if application_id == 0x43455254 and db.execute("PRAGMA user_version").fetchone()[0] != 1:
            raise ValueError("Unsupported research schema version")
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript(SCHEMA)
        db.execute("PRAGMA application_id=1128616532")
        db.execute("PRAGMA user_version=1")
        prior = db.execute("SELECT version FROM datasets WHERE sha256=?", (dataset,)).fetchone()
        if prior and prior[0] != VERSION:
            raise ValueError("Research dataset version mismatch")
        db.execute("INSERT OR IGNORE INTO datasets VALUES (?,?,?)", (dataset, VERSION, result["manifest_sha256"]))
        db.commit()
        for member in selected:
            filename = PurePosixPath(member["name"]).name
            state = db.execute("SELECT cache_hash,processed,valid,inserted,duplicates,invalid FROM progress WHERE dataset_sha256=? AND source_file=?", (dataset, filename)).fetchone()
            counts = [0, 0, 0, 0, 0]
            if state and state[0] == member["cache_hash"]:
                counts = list(state[1:])
            elif state:
                # Prefix extension must preserve every already observed row.
                raise ValueError("Resume prefix changed; retain original inspection")
            goal = min(member["cached_rows"], limit or member["cached_rows"])
            if counts[0] > goal:
                raise ValueError("Requested bound is below already committed progress")
            if goal == 0 and not state:
                db.execute("INSERT INTO progress VALUES (?,?,?,?,?,?,?,?)", (dataset, filename, member["cache_hash"], *counts))
                db.commit()
            with (folder / member["cache"]).open(encoding="utf-8") as stream:
                for index, line in enumerate(stream, 1):
                    if index <= counts[0]:
                        continue
                    if index > goal:
                        break
                    values = json.loads(line)
                    source_row = index
                    if member.get('cache_format') == 'indexed-v1':
                        if (not isinstance(values, dict) or set(values) != {'source_row', 'values'}
                                or not isinstance(values['source_row'], int) or values['source_row'] < index):
                            raise ValueError('Invalid indexed cache')
                        source_row, values = values['source_row'], values['values']
                    try:
                        event = normalize(filename, member["header"], values)
                        previous = db.execute("SELECT row_hash FROM events WHERE dataset_sha256=? AND source_file=? AND source_id=?", (dataset, filename, event["source_id"])).fetchone()
                        if previous and previous[0] != event["row_hash"]:
                            raise ValueError("conflicting_source_id")
                        counts[1] += 1
                        if previous:
                            counts[3] += 1
                        else:
                            db.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                       (dataset, filename, event["source_id"], source_row, event["user"], event["pc"],
                                        event["timestamp_raw"], event["timestamp_local"], "unspecified_release_local",
                                        event["channel"], event["action"], event["resource"], event["metadata_json"], event["row_hash"]))
                            counts[2] += 1
                    except ValueError as error:
                        db.execute("INSERT INTO diagnostics VALUES (?,?,?,?)", (dataset, filename, source_row, str(error)))
                        counts[4] += 1
                    counts[0] += 1
                    if counts[0] % chunk == 0 or counts[0] == goal:
                        if counts[0] != counts[1] + counts[4] or counts[1] != counts[2] + counts[3]:
                            raise AssertionError("Row reconciliation failed")
                        require_space(folder, reserve=reserve)
                        db.execute("INSERT OR REPLACE INTO progress VALUES (?,?,?,?,?,?,?,?)", (dataset, filename, member["cache_hash"], *counts))
                        db.commit()
                        if progress_log:
                            progress_log(encoded({"source": filename, "processed": counts[0], "valid": counts[1],
                                                  "inserted": counts[2], "duplicates": counts[3], "invalid": counts[4]}))
                        if after_chunk:
                            after_chunk(filename, counts[0])
        progress = [dict(zip(("source", "processed", "valid", "inserted", "duplicates", "invalid"), row))
                    for row in db.execute("SELECT source_file,processed,valid,inserted,duplicates,invalid FROM progress WHERE dataset_sha256=? ORDER BY source_file", (dataset,))]
        event_count = db.execute("SELECT count(*) FROM events WHERE dataset_sha256=?", (dataset,)).fetchone()[0]
        error_count = db.execute("SELECT count(*) FROM diagnostics WHERE dataset_sha256=?", (dataset,)).fetchone()[0]
        if event_count != sum(p["inserted"] for p in progress) or error_count != sum(p["invalid"] for p in progress):
            raise AssertionError("Storage reconciliation failed")
        return {"version": VERSION, "dataset_sha256": dataset, "manifest_sha256": result["manifest_sha256"],
                "bound_per_source": limit or result["row_bound_per_member"], "progress": progress,
                "events": event_count, "errors": error_count, "labels_created": False,
                "timezone_basis": "unspecified_release_local", "full_dataset_ingested": not result.get("cohort") and all(m["complete"] and (limit is None or limit >= m["cached_rows"]) for m in selected)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    scan = commands.add_parser("inspect")
    scan.add_argument("--rows", type=int, default=1000)
    scan.add_argument("--max-expanded-gib", type=float, default=32)
    scan.add_argument("--max-cache-mib", type=float, default=128)
    load = commands.add_parser("ingest")
    load.add_argument("--manifest", type=Path, required=True)
    load.add_argument("--limit", type=int)
    load.add_argument("--chunk", type=int, default=500)
    load.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    folder = root / "research/local"
    configuration = json.loads(args.config.read_text())
    database = local_path(folder, Path(configuration["research_database"]))
    if configuration.get("live_database_forbidden") and database.resolve() == Path(configuration["live_database_forbidden"]).resolve():
        raise ValueError("Live database is forbidden")
    if args.command == "inspect":
        manifest = inspect_archive(Path(configuration["r42_archive"]), folder, rows=args.rows,
                                   max_expanded=int(args.max_expanded_gib * 1024**3),
                                   max_cache=int(args.max_cache_mib * 1024**2))
        # Answers are inventoried separately; their prefix cache is never ingested.
        answers = inspect_archive(Path(configuration["answers_archive"]), folder, rows=1,
                                  max_expanded=128 * 1024**2, max_cache=32 * 1024**2)
        result = {"manifest": str(manifest), "answers_manifest": str(answers),
                  "readme": hash_file(Path(configuration["readme"]))}
        atomic_json(folder / "inspection.json", result)
        print(encoded(result))
    else:
        report = local_path(folder, args.report)
        if report.parent != folder or report.suffix != ".json" or report.name in ("inspection.json", "initial_inspection.json") or report == database:
            raise ValueError("Report must be a separate JSON file at research/local root")
        # Validate original content, rather than trusting only cached stat metadata.
        inspection = verified_manifest(args.manifest, folder)
        if hash_file(Path(configuration["r42_archive"])) != inspection["input"]:
            raise ValueError("Source archive no longer matches inspection")
        result = ingest(args.manifest, folder, database, chunk=args.chunk, limit=args.limit)
        atomic_json(report, result)
        print(encoded(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
