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

        changed_since_ts = self._to_epoch(changed_since)
        changed_until_ts = self._to_epoch(changed_until)
        created_since_ts = self._to_epoch(created_since)
        created_until_ts = self._to_epoch(created_until)

        project_filters: list[int | None] = [None] if not projects else [*projects]

        for nid in project_filters:
            params: dict[str, Any] = {"type": "changenotice"}
            if nid is not None:
                params["field_project"] = nid
            if to_branch:
                params["field_change_to_branch"] = to_branch

            for page in self._nodes_api.query_all(**params, max_pages=max_pages):
                for node in page.get("list", []):
                    if not self._matches_time_filters(
                        node,
                        changed_since_ts=changed_since_ts,
                        changed_until_ts=changed_until_ts,
                        created_since_ts=created_since_ts,
                        created_until_ts=created_until_ts,
                    ):
                        continue
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

    @staticmethod
    def _to_epoch(value: str | None) -> int | None:
        if not value:
            return None

        text = value.strip()
        if text.isdigit():
            return int(text)

        try:
            # Accept YYYY-MM-DD and full ISO timestamps
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except ValueError:
            return None

    @staticmethod
    def _node_epoch(node: dict[str, Any], key: str) -> int | None:
        raw = node.get(key)
        if raw is None:
            return None
        text = str(raw).strip()
        if not text:
            return None
        if text.isdigit():
            return int(text)
        try:
            return int(float(text))
        except ValueError:
            return None

    @classmethod
    def _matches_time_filters(
        cls,
        node: dict[str, Any],
        *,
        changed_since_ts: int | None,
        changed_until_ts: int | None,
        created_since_ts: int | None,
        created_until_ts: int | None,
    ) -> bool:
        changed_ts = cls._node_epoch(node, "changed")
        created_ts = cls._node_epoch(node, "created")

        if changed_since_ts is not None and (changed_ts is None or changed_ts < changed_since_ts):
            return False
        if changed_until_ts is not None and (changed_ts is None or changed_ts > changed_until_ts):
            return False
        if created_since_ts is not None and (created_ts is None or created_ts < created_since_ts):
            return False
        if created_until_ts is not None and (created_ts is None or created_ts > created_until_ts):
            return False

        return True
