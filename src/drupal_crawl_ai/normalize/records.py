"""Canonical record normalizers — map raw Drupal API payloads to canonical records."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _ensure_iso(value: Any) -> str:
    """Convert a timestamp (int, float, or numeric string) to ISO-8601 string."""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.isoformat()
        except ValueError:
            # Try parsing as Unix timestamp string
            try:
                dt = datetime.fromtimestamp(int(value))
                return dt.isoformat()
            except (ValueError, OSError):
                return value
    if isinstance(value, (int, float)):
        dt = datetime.fromtimestamp(value)
        return dt.isoformat()
    return str(value)


def _norm_field(value: Any) -> Any:
    """Normalize field values: extract scalar id from entity refs, convert numeric strings to int."""
    if isinstance(value, dict):
        # Entity references come back as {"id": "...", "resource": "...", ...}
        if "id" in value:
            return _norm_field(value["id"])
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return value
    return value


def normalize_issue(raw: dict[str, Any], fetched_at: str) -> dict[str, Any]:
    """
    Normalize a raw Drupal project_issue node to a canonical record.

    Adds record_type, source_url, fetched_at, raw_payload, and normalizes
    date fields to ISO-8601.
    """
    nid = raw.get("nid")
    _body = raw.get("body", {})
    if isinstance(_body, dict):
        body_raw = _body.get("value", "") or ""
    elif isinstance(_body, str):
        body_raw = _body
    else:
        body_raw = ""

    record: dict[str, Any] = {
        "record_type": "project_issue",
        "nid": _norm_field(raw.get("nid")),
        "title": raw.get("title", ""),
        "body": body_raw,
        "raw_body": body_raw,  # preserve original HTML
        "status": raw.get("status", ""),
        "priority": raw.get("priority", ""),
        "created": _ensure_iso(raw.get("created")),
        "changed": _ensure_iso(raw.get("changed")),
        "comment_count": _norm_field(raw.get("comment_count", 0)),
        "field_project": _norm_field(raw.get("field_project")),
        "source_url": f"https://www.drupal.org/api-d7/node/{nid}.json",
        "source_endpoint": "node.json",
        "source_params": {"type": "project_issue"},
        "fetched_at": fetched_at,
        "raw_payload": raw,
    }
    return record


def normalize_comment(raw: dict[str, Any], fetched_at: str) -> dict[str, Any]:
    """
    Normalize a raw Drupal comment to a canonical record.

    Uses ``node`` as the issue NID field per Drupal api-d7 convention.
    """
    cid = raw.get("cid")
    _comment_body = raw.get("comment_body", {})
    if isinstance(_comment_body, dict):
        body_raw = _comment_body.get("value", "") or ""
    elif isinstance(_comment_body, str):
        body_raw = _comment_body
    else:
        body_raw = ""

    record: dict[str, Any] = {
        "record_type": "issue_comment",
        "cid": _norm_field(cid),
        "nid": _norm_field(raw.get("node")),
        "subject": raw.get("subject", ""),
        "body": body_raw,
        "raw_body": body_raw,
        "created": _ensure_iso(raw.get("created")),
        "changed": _ensure_iso(raw.get("changed")),
        "author_name": raw.get("name", ""),
        "author_mail": raw.get("mail", "") or None,
        "source_url": f"https://www.drupal.org/api-d7/comment/{cid}.json",
        "source_endpoint": "comment.json",
        "source_params": {"node": _norm_field(raw.get("node"))},
        "fetched_at": fetched_at,
        "raw_payload": raw,
    }
    return record


def normalize_change_notice(raw: dict[str, Any], fetched_at: str) -> dict[str, Any]:
    """
    Normalize a raw Drupal changenotice node to a canonical record.
    """
    nid = raw.get("nid")
    _body = raw.get("body", {})
    if isinstance(_body, dict):
        body_raw = _body.get("value", "") or ""
    elif isinstance(_body, str):
        body_raw = _body
    else:
        body_raw = ""

    # Change notice primary text is often stored in field_description.
    if not body_raw:
        _description = raw.get("field_description", {})
        if isinstance(_description, dict):
            body_raw = _description.get("value", "") or ""

    record: dict[str, Any] = {
        "record_type": "change_notice",
        "nid": _norm_field(nid),
        "title": raw.get("title", ""),
        "body": body_raw,
        "raw_body": body_raw,
        "field_project": _norm_field(raw.get("field_project")),
        "field_change_to_branch": raw.get("field_change_to_branch", ""),
        "field_issue_links": raw.get("field_issue_links", []),
        "field_issues": raw.get("field_issues", []),
        "field_change_records": raw.get("field_change_records", []),
        "created": _ensure_iso(raw.get("created")),
        "changed": _ensure_iso(raw.get("changed")),
        "source_url": f"https://www.drupal.org/api-d7/node/{nid}.json",
        "source_endpoint": "node.json",
        "source_params": {"type": "changenotice"},
        "fetched_at": fetched_at,
        "raw_payload": raw,
    }
    return record
