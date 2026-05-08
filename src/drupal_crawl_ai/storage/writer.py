"""Unified writer supporting jsonl, markdown, and both output modes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from drupal_crawl_ai.normalize.markdown import MarkdownRenderer
from drupal_crawl_ai.storage.writer_jsonl import JsonlWriter
from drupal_crawl_ai.storage.writer_markdown import MarkdownWriter


class Writer:
    """
    Unified output writer for a single run.

    format modes:
    - ``jsonl``: canonical JSONL only
    - ``markdown``: rendered markdown only
    - ``both``: write both
    """

    def __init__(
        self,
        root: Path,
        run_id: str,
        format: str = "both",
    ) -> None:
        self._root = root
        self._run_id = run_id
        self._format = format
        self._normalized_dir = root / "normalized" / run_id

        self._jsonl_path = self._normalized_dir / "records.jsonl"
        self._jsonl: JsonlWriter | None = None
        self._md: MarkdownWriter | None = None
        self._renderer = MarkdownRenderer()

        if format in ("jsonl", "both"):
            self._jsonl = JsonlWriter(self._jsonl_path)
        if format in ("markdown", "both"):
            self._md = MarkdownWriter(self._normalized_dir / "markdown")

    def write_record(self, record: dict[str, Any]) -> None:
        """Write a canonical record to JSONL and/or markdown."""
        # Ensure deterministic key ordering
        sorted_record = dict(sorted(record.items()))

        if self._jsonl:
            self._jsonl.write(sorted_record)

        if self._md:
            record_type = str(record.get("record_type", "unknown"))
            nid = record.get("nid") or record.get("cid") or 0
            content = self._renderer.render_with_frontmatter(record)
            self._md.write(record_type, nid, content)

    def write_comment(self, comment: dict[str, Any], issue_id: int | str) -> None:
        """Append a comment as a nested section in the parent issue's markdown."""
        if not self._md:
            return

        cid = comment.get("cid", 0)
        comment_body = str(comment.get("comment") or comment.get("body") or "")

        # Append to the issue's markdown file
        issue_path = self._md._root / "project_issue" / f"{issue_id}.md"
        issue_path.parent.mkdir(parents=True, exist_ok=True)
        if issue_path.exists():
            existing = issue_path.read_text(encoding="utf-8")
        else:
            existing = ""

        with open(issue_path, "w", encoding="utf-8") as f:
            f.write(existing + "\n\n## Comment: " + str(cid) + "\n\n" + comment_body + "\n")
