"""Extractor for single issue details."""

from __future__ import annotations

from datetime import datetime, timezone

from drupal_crawl_ai.api.nodes import NodesApi
from drupal_crawl_ai.config import Config
from drupal_crawl_ai.normalize.records import normalize_issue


class IssueDetailsExtractor:
    def __init__(
        self,
        nodes_api: NodesApi | None = None,
        config: Config | None = None,
    ) -> None:
        self._nodes_api = nodes_api or NodesApi(config=config)
        self._config = config or Config()

    def extract(
        self,
        *,
        nid: int,
        include_related_mrs: bool = False,
        include_extra_credit: bool = False,
    ) -> dict[str, object]:
        fetched_at = datetime.now(timezone.utc).isoformat()
        node = self._nodes_api.get_node(nid)
        return normalize_issue(node, fetched_at)
