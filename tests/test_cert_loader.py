"""Tiny fabricated format fixtures, unrelated to real CERT records."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ml.data.loader import iter_records


def test_missing_input_and_columns(tmp_path):
    with pytest.raises(FileNotFoundError):
        list(iter_records(tmp_path / "missing"))
    (tmp_path / "file.csv").write_text("id,date,user\n1,2026-01-01,synthetic\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing columns"):
        list(iter_records(tmp_path))


def test_synthetic_mapping(tmp_path):
    (tmp_path / "device.csv").write_text("id,date,user,pc,activity\nsynthetic-1,01/01/2026 12:00:00,fake.user,FAKE-PC,connect\n", encoding="utf-8")
    rows = list(iter_records(tmp_path))
    assert len(rows) == 1
    assert rows[0]["channel"] == "USB"
    assert rows[0]["event_type"] == "USB_CONNECT"
    assert rows[0]["timestamp"].endswith("+00:00")
