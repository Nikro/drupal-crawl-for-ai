"""Unit tests for CommentsApi."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from drupal_crawl_ai.api.comments import CommentsApi
from drupal_crawl_ai.config import Config
from drupal_crawl_ai.http.cache import ResponseCache


def _isolated_comments_api(tmp_path: Path) -> CommentsApi:
    cfg = Config()
    cfg.cache._cache_root = tmp_path  # type: ignore[assignment]
    cache = ResponseCache(cfg)
    cache._cached_dir = tmp_path  # type: ignore[assignment]
    return CommentsApi(cache=cache, config=cfg)


def test_query_uses_node_filter_key(tmp_path: Path) -> None:
    """Verify that comments are fetched with 'node' filter, not 'nid'."""
    api = _isolated_comments_api(tmp_path)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"list": []}'
    mock_response.json.return_value = {"list": []}

    mock_get = patch.object(api._client, "get", return_value=mock_response)
    mocked = mock_get.start()
    try:
        api.query(node=12345)
    finally:
        mock_get.stop()

    # Verify 'node' was in the params — params are 2nd positional arg
    call_args = mocked.call_args
    assert call_args is not None
    params = call_args[0][1]  # positional: (url, params_dict)
    assert "node" in params
    assert "nid" not in params


def test_query_caches_response(tmp_path: Path) -> None:
    api = _isolated_comments_api(tmp_path)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"list": []}'
    mock_response.json.return_value = {"list": []}

    mock_get = patch.object(api._client, "get", return_value=mock_response)
    mocked = mock_get.start()
    try:
        api.query(node=12345)
        api.query(node=12345)
    finally:
        mock_get.stop()

    assert mocked.call_count == 1


def test_query_all_returns_pages(tmp_path: Path) -> None:
    api = _isolated_comments_api(tmp_path)

    page1 = {"list": [{"cid": 1}], "next": "http://example.com/comment.json?page=1"}
    page2 = {"list": [{"cid": 2}], "next": None}

    with patch.object(api, "query", side_effect=[page1, page2]):
        pages = list(api.query_all(node=12345))
        assert len(pages) == 2
