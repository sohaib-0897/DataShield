"""Run existing upstream tests in a temporary source copy, never a live database."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
    with tempfile.TemporaryDirectory(prefix="datashield-upstream-baseline-") as sandbox:
        folder = Path(sandbox)
        for name in tracked:
            if name and (name.endswith(".py") or name == "pytest.ini"):
                target = folder / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(root / name, target)
        env = dict(os.environ, DATABASE_URL="sqlite://", PYTHONDONTWRITEBYTECODE="1",
                   DATASHIELD_JWT_SECRET="synthetic-phase0-jwt-secret-32-characters",
                   DATASHIELD_AGENT_KEY="synthetic-phase0-agent-secret-32-characters")
        for name in ("DATASHIELD_ANOMALY_ARTIFACT", "DATASHIELD_SENSITIVITY_ARTIFACT",
                     "DATASHIELD_SPAN_ARTIFACT", "DATASHIELD_SPAN_SELECTION_SHA256", "DATASHIELD_SPAN_ADVISORY_ENABLED"):
            env.pop(name, None)
        env["DATASHIELD_MODEL_ROOT"] = str(folder / "isolated-models")
        result = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                                cwd=folder, env=env, capture_output=True, text=True)
    args.log.parent.mkdir(parents=True, exist_ok=True)
    args.log.write_text(result.stdout + result.stderr)
    summary = result.stdout.splitlines()[-12:]
    report = {"python": sys.version.split()[0], "exit_code": result.returncode,
              "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
              "isolation": "tracked Python/config copied to temporary directory; DATABASE_URL=sqlite://; existing test_api DB also inside temporary copy",
              "collection_errors": re.findall(r"^ERROR (tests/[^\s]+)", result.stdout, re.MULTILINE),
              "summary": summary, "node_available": bool(shutil.which("node")),
              "npm_available": bool(shutil.which("npm")), "log": str(args.log)}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"exit_code": result.returncode, "collection_errors": len(report["collection_errors"]),
                      "summary": summary[-2:], "report": str(args.report)}))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
