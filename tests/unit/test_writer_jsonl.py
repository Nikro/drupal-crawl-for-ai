"""Unit tests for JsonlWriter."""

from __future__ import annotations

import json

from drupal_crawl_ai.storage.writer_jsonl import JsonlWriter


def test_write_single_record(tmp_path):
    path = tmp_path / "records.jsonl"
    writer = JsonlWriter(path)
    writer.write({"nid": 123, "title": "Test issue"})
    lines = path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    assert json.loads(lines[0])["nid"] == 123


def test_write_batch(tmp_path):
    path = tmp_path / "records.jsonl"
    writer = JsonlWriter(path)
    writer.write_batch([{"nid": 1}, {"nid": 2}, {"nid": 3}])
    lines = path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3


def test_each_line_parses_to_dict(tmp_path):
    path = tmp_path / "records.jsonl"
    writer = JsonlWriter(path)
    writer.write({"type": "issue", "nid": 1})
    writer.write({"type": "comment", "cid": 2})
    for line in path.read_text(encoding="utf-8").strip().split("\n"):
        parsed = json.loads(line)
        assert isinstance(parsed, dict)


def test_file_is_utf8(tmp_path):
    path = tmp_path / "records.jsonl"
    writer = JsonlWriter(path)
    writer.write({"title": "Héllo Wörld"})
    raw = path.read_bytes()
    raw.decode("utf-8")


def test_append_safe(tmp_path):
    path = tmp_path / "records.jsonl"
    writer = JsonlWriter(path)
    writer.write({"nid": 1})
    writer.write({"nid": 2})
    writer.write({"nid": 3})
    lines = path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3


def test_deterministic_key_order(tmp_path):
    path = tmp_path / "records.jsonl"
    writer = JsonlWriter(path)
    writer.write({"z": 1, "a": 2, "m": 3})
    line = path.read_text(encoding="utf-8").strip()
    assert line.index('"a"') < line.index('"m"') < line.index('"z"')
