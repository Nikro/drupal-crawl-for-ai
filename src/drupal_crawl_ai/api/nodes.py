"""Node API helper for querying Drupal.org api-d7/node.json."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from drupal_crawl_ai.api.pagination import paginate
from drupal_crawl_ai.config import Config
from drupal_crawl_ai.http.cache import ResponseCache
from drupal_crawl_ai.http.client import DrupalClient


class NodesApi:
    """Helper for querying Drupal.org node API endpoints with transparent caching."""

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
        page: int = 0,
        limit: int = 50,
        _absolute_url: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Fetch a single page of nodes matching the given filters.

        Filters are passed as query params (e.g. type="project_issue").
        Params are sorted for deterministic cache keys.

        ``_absolute_url`` is internal-only: used by ``query_all`` when following
        Drupal's absolute ``next`` URLs so the URL is used as-is without joining
        against the base URL.
        """
        params = {"page": page, "limit": limit, **kwargs}
        if _absolute_url:
            url = _absolute_url
        else:
            url = f"{self._base}/node.json"

        # Check cache first
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
        max_pages: int = 20,
        **kwargs: Any,
    ) -> Iterator[dict[str, Any]]:
        """
        Iterate over all pages of nodes matching the given filters.

        Uses transparent read-through caching and follows pagination automatically.
        """
        def fetch_page(next_url: str | None) -> dict[str, Any]:
            if next_url is None:
                params: dict[str, Any] = {"page": 0, "limit": 50, **kwargs}
                return self.query(**params)

            # The Drupal api-d7 "next" field returns an absolute URL.
            # Extract the relative path and query params so query() can
            # reconstruct the URL correctly via its own base_url.
            from urllib.parse import parse_qs, urlparse

            parsed = urlparse(next_url)
            params = dict(parse_qs(parsed.query))
            # parse_qs returns lists for all values — normalize to scalars
            params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
            # Construct absolute URL from next URL parts (path may or may not
            # include "api-d7" prefix — use scheme+netloc from next URL to be safe)
            absolute_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            return self.query(**params, _absolute_url=absolute_url)

        return paginate(fetch_page, max_pages=max_pages)

    def get_node(self, nid: int) -> dict[str, Any]:
        """Fetch a single node by NID."""
        url = f"{self._base}/node/{nid}.json"

        cached = self._cache.get("GET", url, None)
        if cached:
            return cached["body"]  # type: ignore[no-any-return]

        response = self._client.get(url)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        self._cache.set("GET", url, None, response)
        return data
