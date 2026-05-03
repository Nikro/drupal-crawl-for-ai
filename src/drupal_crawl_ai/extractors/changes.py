"""Extractor for Drupal change notices (type=changenotice)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from drupal_crawl_ai.api.nodes import NodesApi
from drupal_crawl_ai.config import Config
from drupal_crawl_ai.normalize.records import normalize_change_notice
from drupal_crawl_ai.storage.manifest import RunManifest
from drupal_crawl_ai.storage.writer import Writer


class ChangesExtractor:
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
        to_branch: str | None = None,
        changed_since: str | None = None,
        changed_until: str | None = None,
        created_since: str | None = None,
        created_until: str | None = None,
        max_pages: int = 20,
    ) -> None:
        fetched_at = datetime.now(timezone.utc).isoformat()

        for nid in projects:
            params: dict[str, Any] = {"type": "changenotice", "field_project": nid}
            if changed_since:
                params["changed_after"] = changed_since
            if changed_until:
                params["changed_before"] = changed_until
            if created_since:
                params["created_after"] = created_since
            if created_until:
                params["created_before"] = created_until

            for page in self._nodes_api.query_all(**params, max_pages=max_pages):
                for node in page.get("list", []):
                    if self._manifest:
                        self._manifest.increment("fetched")
                    try:
                        record = normalize_change_notice(node, fetched_at)
                        if self._writer:
                            self._writer.write_record(record)
                        if self._manifest:
                            self._manifest.increment("succeeded")
                    except Exception as exc:
                        url = f"https://www.drupal.org/api-d7/node/{node.get('nid')}.json"
                        if self._manifest:
                            self._manifest.record_failure(url, 0, str(exc), node.get("nid"))
