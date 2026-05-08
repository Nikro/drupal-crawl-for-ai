"""Unit tests for record normalizers."""

from __future__ import annotations

from drupal_crawl_ai.normalize.records import (
    normalize_change_notice,
    normalize_comment,
    normalize_issue,
)


def test_normalize_issue_adds_record_type():
    raw = {"nid": 123, "title": "Bug fix", "status": "Active", "priority": "Normal"}
    result = normalize_issue(raw, "2025-01-01T00:00:00Z")
    assert result["record_type"] == "project_issue"


def test_normalize_issue_preserves_raw_payload():
    raw = {"nid": 123, "title": "Test", "custom_field": "value"}
    result = normalize_issue(raw, "2025-01-01T00:00:00Z")
    assert result["raw_payload"] == raw
    assert result["raw_payload"]["custom_field"] == "value"


def test_normalize_issue_normalizes_dates():
    import time
    raw = {"nid": 123, "title": "Test", "created": int(time.time()), "changed": int(time.time())}
    result = normalize_issue(raw, "2025-01-01T00:00:00Z")
    assert "T" in result["created"]
    assert "T" in result["changed"]


def test_normalize_issue_adds_provenance():
    raw = {"nid": 12345}
    result = normalize_issue(raw, "2025-01-01T00:00:00Z")
    assert "source_url" in result
    assert "fetched_at" in result
    assert result["source_url"] == "https://www.drupal.org/api-d7/node/12345.json"


def test_normalize_issue_field_project_converted_to_int():
    raw = {"nid": 123, "field_project": "3060"}
    result = normalize_issue(raw, "2025-01-01T00:00:00Z")
    assert result["field_project"] == 3060
    assert isinstance(result["field_project"], int)


def test_normalize_comment():
    raw = {"cid": 999, "node": 12345, "subject": "Re: Test", "name": "user@example.com"}
    result = normalize_comment(raw, "2025-01-01T00:00:00Z")
    assert result["record_type"] == "issue_comment"
    assert result["cid"] == 999
    assert result["nid"] == 12345
    assert result["author_name"] == "user@example.com"


def test_normalize_change_notice():
    raw = {
        "nid": 555,
        "title": "Change",
        "field_project": "3060",
        "field_change_to_branch": "11.x",
        "field_issue_links": [{"url": "https://www.drupal.org/node/123"}],
    }
    result = normalize_change_notice(raw, "2025-01-01T00:00:00Z")
    assert result["record_type"] == "change_notice"
    assert result["nid"] == 555
    assert result["field_change_to_branch"] == "11.x"
    assert result["field_issue_links"][0]["url"].endswith("/123")


def test_normalize_change_notice_uses_field_description_when_body_empty():
    raw = {
        "nid": 556,
        "title": "Change",
        "body": [],
        "field_description": {"value": "<p>Primary change text</p>"},
    }
    result = normalize_change_notice(raw, "2025-01-01T00:00:00Z")
    assert result["body"] == "<p>Primary change text</p>"


def test_normalize_missing_fields_handled_gracefully():
    raw = {}
    result = normalize_issue(raw, "2025-01-01T00:00:00Z")
    assert result["record_type"] == "project_issue"
    assert result["nid"] is None
