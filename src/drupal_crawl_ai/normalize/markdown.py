"""Markdown renderer — convert Drupal HTML body fields to readable markdown."""

from __future__ import annotations

import html2text


class MarkdownRenderer:
    """
    Render Drupal HTML body content to Markdown using html2text.

    Settings are deterministic to ensure same input always produces same output.
    """

    def __init__(self) -> None:
        self._h2t = html2text.HTML2Text()
        self._h2t.body_width = 0  # no wrapping
        self._h2t.escape_snob = False
        self._h2t.links_each_paragraph = True
        self._h2t.skip_internal_links = True
        self._h2t.unicode_snob = True

    def render(self, html_body: str) -> str:
        """Convert HTML body to markdown. Empty input returns empty string."""
        if not html_body:
            return ""
        return self._h2t.handle(html_body).strip()

    def render_with_frontmatter(self, record: dict[str, object]) -> str:
        """
        Render a canonical record to markdown with a YAML-like frontmatter header.

        The frontmatter includes: record_type, id, fetched_at, source_url
        """
        record_type = str(record.get("record_type", ""))
        nid = record.get("nid")
        cid = record.get("cid")
        entity_id = nid or cid or ""
        fetched_at = str(record.get("fetched_at", ""))
        source_url = str(record.get("source_url", ""))
        body_markdown = self.render(str(record.get("body", "")))

        lines = [
            "---",
            f"record_type: {record_type}",
            f"id: {entity_id}",
            f"fetched_at: {fetched_at}",
            f"source_url: {source_url}",
            "---",
            "",
            body_markdown,
        ]
        return "\n".join(lines) + "\n"
