"""Unit tests for MarkdownWriter."""

from __future__ import annotations

from drupal_crawl_ai.storage.writer_markdown import MarkdownWriter


def test_write_returns_correct_path(tmp_path):
    writer = MarkdownWriter(tmp_path)
    path = writer.write("project_issue", 12345, "# Test Issue\n\nBody content.")
    assert path == tmp_path / "project_issue" / "12345.md"


def test_write_creates_intermediate_dirs(tmp_path):
    writer = MarkdownWriter(tmp_path)
    writer.write("deep/nested/type", 1, "Content")
    assert (tmp_path / "deep" / "nested" / "type" / "1.md").exists()


def test_overwrite_is_idempotent(tmp_path):
    writer = MarkdownWriter(tmp_path)
    writer.write("project_issue", 123, "Version 1")
    writer.write("project_issue", 123, "Version 2")
    assert (tmp_path / "project_issue" / "123.md").exists()
    assert (tmp_path / "project_issue" / "123.md").read_text() == "Version 2"


def test_content_written_correctly(tmp_path):
    writer = MarkdownWriter(tmp_path)
    content = "# Hello\n\nThis is the body."
    writer.write("change_notice", 999, content)
    assert (tmp_path / "change_notice" / "999.md").read_text() == content
