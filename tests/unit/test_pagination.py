"""Unit tests for pagination helper."""

from __future__ import annotations

from drupal_crawl_ai.api.pagination import extract_next_url, paginate


def test_extract_next_url() -> None:
    assert extract_next_url({"next": "https://api.example.com/node.json?page=2"}) == "https://api.example.com/node.json?page=2"
    assert extract_next_url({}) is None
    assert extract_next_url({"next": None}) is None


def test_paginate_stops_on_missing_next() -> None:
    pages = [
        {"list": [{"nid": 1}], "next": None},
    ]
    fetched: list[str | None] = []

    def fake_fetch(url: str | None) -> dict:
        fetched.append(url)
        return pages[len(fetched) - 1]

    result = list(paginate(fake_fetch))
    assert len(result) == 1
    assert fetched == [None]


def test_paginate_stops_on_empty_list() -> None:
    pages = [
        {"list": [{"nid": 1}], "next": "https://api.example.com/page=2"},
        {"list": [], "next": None},
    ]
    fetched: list[str | None] = []

    def fake_fetch(url: str | None) -> dict:
        fetched.append(url)
        return pages[len(fetched) - 1]

    result = list(paginate(fake_fetch))
    # Empty list stops iteration — the empty page is NOT yielded
    assert len(result) == 1
    assert result[0]["list"] == [{"nid": 1}]


def test_paginate_respects_max_pages() -> None:
    pages = [{"list": [{"nid": i}], "next": f"https://api.example.com/page={i+1}"} for i in range(1, 31)]
    fetched: list[str | None] = []

    def fake_fetch(url: str | None) -> dict:
        idx = len(fetched)
        fetched.append(url)
        return pages[idx] if idx < len(pages) else {"list": [], "next": None}

    result = list(paginate(fake_fetch, max_pages=5))
    assert len(result) == 5
    assert fetched == [None] + [f"https://api.example.com/page={i}" for i in range(2, 6)]


def test_paginate_no_pages() -> None:
    def fake_fetch(url: str | None) -> dict:
        return {"list": [], "next": None}

    result = list(paginate(fake_fetch))
    assert result == []
