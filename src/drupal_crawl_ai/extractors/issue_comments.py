"""Extractor for issue comments."""

from __future__ import annotations

from datetime import datetime, timezone

from drupal_crawl_ai.api.comments import CommentsApi
from drupal_crawl_ai.config import Config
from drupal_crawl_ai.normalize.records import normalize_comment
from drupal_crawl_ai.storage.manifest import RunManifest
from drupal_crawl_ai.storage.writer import Writer


class IssueCommentsExtractor:
    def __init__(
        self,
        comments_api: CommentsApi | None = None,
        writer: Writer | None = None,
        manifest: RunManifest | None = None,
        config: Config | None = None,
    ) -> None:
        self._comments_api = comments_api or CommentsApi(config=config)
        self._writer = writer
        self._manifest = manifest
        self._config = config or Config()

    def extract(
        self,
        *,
        issue_nid: int,
        max_pages: int = 20,
    ) -> None:
        fetched_at = datetime.now(timezone.utc).isoformat()

        for page in self._comments_api.query_all(node=issue_nid, max_pages=max_pages):
            for comment in page.get("list", []):
                if self._manifest:
                    self._manifest.increment("fetched")
                try:
                    record = normalize_comment(comment, fetched_at)
                    if self._writer:
                        self._writer.write_comment(record, issue_nid)
                        self._writer.write_record(record)
                    if self._manifest:
                        self._manifest.increment("succeeded")
                except Exception as exc:
                    cid = comment.get("cid", "unknown")
                    url = f"https://www.drupal.org/api-d7/comment/{cid}.json"
                    if self._manifest:
                        self._manifest.record_failure(url, 0, str(exc), cid)
