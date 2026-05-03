"""Project discovery and alias resolution — API-first."""

from __future__ import annotations

from drupal_crawl_ai.config import Config
from drupal_crawl_ai.http.client import DrupalClient


def resolve_project(
    identifier: int | str,
    allow_html_fallback: bool = False,
    client: DrupalClient | None = None,
    config: Config | None = None,
) -> int:
    """
    Resolve a project identifier (NID or alias) to a numeric NID.

    - If ``identifier`` is numeric string or int → return as int directly
    - If ``identifier`` is a string alias → query api-d7 node by
      ``field_project_short_name`` filter
    - If alias cannot be resolved and ``allow_html_fallback=False`` →
      raise ValueError(f"Cannot resolve project alias: {identifier}")
    - If alias cannot be resolved and ``allow_html_fallback=True`` → return 0
    """
    if str(identifier).isdigit():
        return int(identifier)

    _client = client or DrupalClient(config)
    url = f"{_client._http.base_url}/node.json"
    params = {"field_project_short_name": str(identifier), "type": "project", "limit": 1}

    try:
        response = _client.get(url, params)
        if response.status_code == 200:
            data = response.json()
            nodes = data.get("list", [])
            if nodes:
                return int(nodes[0]["nid"])
    except Exception:
        pass

    if not allow_html_fallback:
        raise ValueError(f"Cannot resolve project alias: {identifier}")

    return 0
