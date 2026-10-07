"""Record/compare source and live-file hashes without opening SQLite or policy data.

Archives use size/mtime/inode observations in Phase 0; full source archive hashes
belong to Phase 1. This never extracts archives or reads document contents.
"""
import argparse
import hashlib
import json
from pathlib import Path


def snapshot(source, dataset):
    paths = set(source.glob("*.py")) | set(source.glob("*.html"))
    live = source / "data"
    if live.exists():
        paths |= {p for p in live.rglob("*") if p.is_file()}
    files = {}
    for path in sorted(paths):
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        stat = path.stat()
        files[str(path.relative_to(source))] = {"sha256": digest.hexdigest(), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    archives = {}
    for name in ("r4.2.tar.bz2", "answers.tar.bz2", "SEI_Insider_README.txt"):
        path = dataset / name
        if path.exists():
            stat = path.stat()
            archives[name] = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "inode": stat.st_ino}
        else:
            archives[name] = None
    return {"source_root": str(source), "dataset_root": str(dataset), "source_and_live_files": files,
            "dataset_stat_only": archives, "archive_contents_hashed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    report = snapshot(args.source_root.resolve(), args.dataset_root.resolve())
    same = True
    if args.compare:
        prior = json.loads(args.compare.read_text())
        same = all(report[k] == prior[k] for k in ("source_root", "dataset_root", "source_and_live_files", "dataset_stat_only"))
        report["matches_before"] = same
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Source/live files: {len(report['source_and_live_files'])}; archive stats: {len(report['dataset_stat_only'])}; unchanged: {same if args.compare else 'baseline recorded'}")
    return 0 if same else 1


if __name__ == "__main__":
    raise SystemExit(main())
