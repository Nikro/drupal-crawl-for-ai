"""Extractor for Drupal issue queues (type=project_issue)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from drupal_crawl_ai.api.nodes import NodesApi
from drupal_crawl_ai.config import Config
from drupal_crawl_ai.normalize.records import normalize_issue
from drupal_crawl_ai.storage.manifest import RunManifest
from drupal_crawl_ai.storage.writer import Writer


class IssuesExtractor:
    def __init__(
        self,
        nodes_api: NodesApi | None = None,
        writer: Writer | None = None,
        manifest: RunManifest | None = None,
        config: Config | None = None,
    ) -> None:
        self._nodes_api = nodes_api or NodesApi(config=config)
        self._writer = writer
        self._manifest = manifest
        self._config = config or Config()

    def extract(
        self,
        *,
        projects: list[int],
        status: str = "any",
        priority: str | None = None,
        changed_since: str | None = None,
        changed_until: str | None = None,
        max_pages: int = 20,
        max_issues: int | None = None,
    ) -> None:
        fetched_at = datetime.now(timezone.utc).isoformat()
        seen_ids: set[int] = set()
        issue_count = 0

        for nid in projects:
            params: dict[str, Any] = {"type": "project_issue", "field_project": nid}
            if changed_since:
                params["changed_after"] = changed_since
            if changed_until:
                params["changed_before"] = changed_until

            for page in self._nodes_api.query_all(**params, max_pages=max_pages):
                for node in page.get("list", []):
                    node_nid = int(node.get("nid", 0))
                    if node_nid in seen_ids:
                        if self._manifest:
                            self._manifest.increment("skipped_duplicates")
                        continue
                    if max_issues and issue_count >= max_issues:
                        return

                    seen_ids.add(node_nid)
                    issue_count += 1
                    if self._manifest:
                        self._manifest.increment("fetched")

                    try:
                        record = normalize_issue(node, fetched_at)
                        if self._writer:
                            self._writer.write_record(record)
                        if self._manifest:
                            self._manifest.increment("succeeded")
                    except Exception as exc:
                        url = f"https://www.drupal.org/api-d7/node/{node_nid}.json"
                        if self._manifest:
                            self._manifest.record_failure(url, 0, str(exc), node_nid)
