"""Unit tests for NodesApi."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from drupal_crawl_ai.api.nodes import NodesApi
from drupal_crawl_ai.config import Config
from drupal_crawl_ai.http.cache import ResponseCache


def _isolated_nodes_api(tmp_path: Path) -> NodesApi:
    cfg = Config()
    cfg.cache._cache_root = tmp_path  # type: ignore[assignment]
    cache = ResponseCache(cfg)
    cache._cached_dir = tmp_path  # type: ignore[assignment]
    return NodesApi(cache=cache, config=cfg)


def test_query_uses_cache(tmp_path: Path) -> None:
    api = _isolated_nodes_api(tmp_path)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"list": []}'
    mock_response.json.return_value = {"list": []}

    mock_get = patch.object(api._client, "get", return_value=mock_response)
    mocked = mock_get.start()
    try:
        api.query(type="project_issue")
        api.query(type="project_issue")
    finally:
        mock_get.stop()

    # Second call should have hit cache — get is called only once
    assert mocked.call_count == 1


def test_query_all_returns_pages(tmp_path: Path) -> None:
    api = _isolated_nodes_api(tmp_path)

    page1 = {"list": [{"nid": 1}], "next": "http://example.com/node.json?page=1"}
    page2 = {"list": [{"nid": 2}], "next": None}

    with patch.object(api, "query", side_effect=[page1, page2]):
        pages = list(api.query_all(type="project_issue"))
        assert len(pages) == 2
