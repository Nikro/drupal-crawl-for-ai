"""Unit tests for unified Writer."""
from __future__ import annotations

from drupal_crawl_ai.storage.writer import Writer


def test_jsonl_mode_creates_jsonl_file(tmp_path) -> None:
    writer = Writer(tmp_path, "run1", format="jsonl")
    writer.write_record({"record_type": "project_issue", "nid": 123, "body": "Test"})
    jsonl_path = tmp_path / "normalized" / "run1" / "records.jsonl"
    assert jsonl_path.exists()


def test_markdown_mode_creates_markdown_file(tmp_path) -> None:
    writer = Writer(tmp_path, "run1", format="markdown")
    writer.write_record({"record_type": "project_issue", "nid": 123, "body": "Test"})
    md_path = tmp_path / "normalized" / "run1" / "markdown" / "project_issue" / "123.md"
    assert md_path.exists()


def test_both_mode_creates_both(tmp_path) -> None:
    writer = Writer(tmp_path, "run1", format="both")
    writer.write_record({"record_type": "project_issue", "nid": 123, "body": "Test"})
    assert (tmp_path / "normalized" / "run1" / "records.jsonl").exists()
    assert (tmp_path / "normalized" / "run1" / "markdown" / "project_issue" / "123.md").exists()


def test_write_record_with_record_type_and_id(tmp_path) -> None:
    writer = Writer(tmp_path, "run1", format="jsonl")
    writer.write_record({"record_type": "change_notice", "nid": 456, "body": "Change"})
    import json
    line = (tmp_path / "normalized" / "run1" / "records.jsonl").read_text()
    parsed = json.loads(line.strip())
    assert parsed["record_type"] == "change_notice"
    assert parsed["nid"] == 456


def test_deterministic_jsonl_key_order(tmp_path) -> None:
    writer = Writer(tmp_path, "run1", format="jsonl")
    writer.write_record({"z": 1, "a": 2, "record_type": "x", "nid": 0})
    line = (tmp_path / "normalized" / "run1" / "records.jsonl").read_text().strip()
    # "a" must come before "n" which must come before "z"
    assert line.index('"a"') < line.index('"nid"') < line.index('"z"')
