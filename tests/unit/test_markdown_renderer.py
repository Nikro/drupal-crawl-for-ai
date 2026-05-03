"""Unit tests for MarkdownRenderer."""

from __future__ import annotations

from drupal_crawl_ai.normalize.markdown import MarkdownRenderer


def test_render_converts_html_to_markdown():
    renderer = MarkdownRenderer()
    html = "<p>Hello <strong>world</strong></p>"
    md = renderer.render(html)
    assert "Hello" in md
    assert "world" in md


def test_render_preserves_links():
    renderer = MarkdownRenderer()
    html = '<p>See <a href="https://example.com">this link</a></p>'
    md = renderer.render(html)
    assert "this link" in md
    assert "https://example.com" in md


def test_render_with_frontmatter_includes_metadata():
    renderer = MarkdownRenderer()
    record = {
        "record_type": "project_issue",
        "nid": 123,
        "body": "<p>Test body</p>",
        "fetched_at": "2025-01-01T00:00:00Z",
        "source_url": "https://www.drupal.org/node/123",
    }
    md = renderer.render_with_frontmatter(record)
    assert "record_type: project_issue" in md
    assert "id: 123" in md
    assert "fetched_at: 2025-01-01T00:00:00Z" in md


def test_deterministic_output_same_input_twice():
    renderer = MarkdownRenderer()
    html = "<p>Test <strong>content</strong></p>"
    md1 = renderer.render(html)
    md2 = renderer.render(html)
    assert md1 == md2


def test_render_empty_body_returns_empty_string():
    renderer = MarkdownRenderer()
    assert renderer.render("") == ""


def test_render_with_frontmatter_body_is_rendered_markdown():
    renderer = MarkdownRenderer()
    record = {
        "record_type": "project_issue",
        "nid": 1,
        "body": "<p>Para</p>",
        "fetched_at": "2025-01-01T00:00:00Z",
        "source_url": "http://example.com",
    }
    md = renderer.render_with_frontmatter(record)
    frontmatter_end = md.index("---", 4)
    body_section = md[frontmatter_end + 4:]
    assert "Para" in body_section
