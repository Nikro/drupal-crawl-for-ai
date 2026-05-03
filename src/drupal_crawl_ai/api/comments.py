"""Comment API helper for querying Drupal.org api-d7/comment.json."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from drupal_crawl_ai.api.pagination import paginate
from drupal_crawl_ai.config import Config
from drupal_crawl_ai.http.cache import ResponseCache
from drupal_crawl_ai.http.client import DrupalClient


class CommentsApi:
    """
    Helper for querying Drupal.org comment API endpoints with transparent caching.

    Uses ``comment.json?node=<nid>`` as documented (not ``nid``).
    """

    def __init__(
        self,
        client: DrupalClient | None = None,
        cache: ResponseCache | None = None,
        config: Config | None = None,
    ) -> None:
        self._client = client or DrupalClient(config)
        self._cache = cache or ResponseCache(config)
        self._config = config or Config()
        self._base = self._config.http.base_url

    def query(
        self,
        *,
        node: int,
        page: int = 0,
        limit: int = 50,
        sort: str = "created",
        direction: str = "ASC",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Fetch a single page of comments for issue node ``node``.

        Note: uses ``node`` filter key (not ``nid``) as required by Drupal api-d7.
        """
        params: dict[str, Any] = {
            "node": node,
            "page": page,
            "limit": limit,
            "sort": sort,
            "direction": direction,
            **kwargs,
        }
        url = f"{self._base}/comment.json"

        cached = self._cache.get("GET", url, params)
        if cached:
            return cached["body"]  # type: ignore[no-any-return]

        response = self._client.get(url, params)
        response.raise_for_status()
        data: dict[str, Any] = response.json()

        self._cache.set("GET", url, params, response)
        return data

    def query_all(
        self,
        *,
        node: int,
        max_pages: int = 20,
        **kwargs: Any,
    ) -> Iterator[dict[str, Any]]:
        """
        Iterate over all pages of comments for issue ``node``.

        Uses transparent read-through caching and follows pagination automatically.
        """
        def fetch_page(next_url: str | None) -> dict[str, Any]:
            if next_url is None:
                return self.query(node=node, **kwargs)
            else:
                from urllib.parse import parse_qs, urlparse
                parsed = urlparse(next_url)
                raw_params: dict[str, list[str]] = parse_qs(parsed.query)
                # Normalize parse_qs output: single-element lists → scalar
                params: dict[str, Any] = {
                    k: v[0] if len(v) == 1 else v[0]
                    for k, v in raw_params.items()
                }
                return self.query(**params)

        return paginate(fetch_page, max_pages=max_pages)
