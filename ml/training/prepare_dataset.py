"""Prepare supplied CERT-like CSVs without loading them all into memory."""
import argparse
import json
from pathlib import Path

from ml.data.loader import SOURCES, iter_records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="ml/data/prepared/events.jsonl")
    args = parser.parse_args()
    input_dir = Path(args.input)
    if not input_dir.is_dir() or not any((input_dir / name).is_file() for name in SOURCES):
        parser.error(f"No supported dataset files found in {input_dir}; supply file.csv, device.csv or http.csv locally")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    valid = invalid = 0
    try:
        with output.open("w", encoding="utf-8") as stream:
            for row in iter_records(args.input):
                if "invalid" in row:
                    invalid += 1
                    continue
                stream.write(json.dumps(row) + "\n")
                valid += 1
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps({"valid": valid, "invalid": invalid, "output": str(output)}))


if __name__ == "__main__": main()
