"""Full issue bundle orchestrator."""

from __future__ import annotations

from drupal_crawl_ai.api.nodes import NodesApi
from drupal_crawl_ai.config import Config
from drupal_crawl_ai.extractors.issue_comments import IssueCommentsExtractor
from drupal_crawl_ai.extractors.issue_details import IssueDetailsExtractor
from drupal_crawl_ai.extractors.issues import IssuesExtractor
from drupal_crawl_ai.storage.manifest import RunManifest
from drupal_crawl_ai.storage.writer import Writer


class IssueBundleExtractor:
    def __init__(
        self,
        writer: Writer | None = None,
        manifest: RunManifest | None = None,
        config: Config | None = None,
    ) -> None:
        self._writer = writer
        self._manifest = manifest
        self._config = config or Config()
        self._nodes_api = NodesApi(config=config)
        self._issues_extractor = IssuesExtractor(
            nodes_api=self._nodes_api,
            writer=writer,
            manifest=manifest,
            config=config,
        )
        self._details_extractor = IssueDetailsExtractor(
            nodes_api=self._nodes_api,
            config=config,
        )
        self._comments_extractor = IssueCommentsExtractor(
            writer=writer,
            manifest=manifest,
            config=config,
        )

    def extract(
        self,
        *,
        projects: list[int],
        include_related_mrs: bool = False,
        include_extra_credit: bool = False,
        max_issues: int | None = None,
        max_pages: int = 20,
    ) -> None:
        # Collect all issue nids across projects
        all_nids: list[int] = []
        seen: set[int] = set()

        for nid in projects:
            params = {"type": "project_issue", "field_project": nid}
            for page in self._nodes_api.query_all(**params, max_pages=max_pages):
                for node in page.get("list", []):
                    node_nid = int(node.get("nid", 0))
                    if node_nid and node_nid not in seen:
                        seen.add(node_nid)
                        if max_issues is None or len(all_nids) < max_issues:
                            all_nids.append(node_nid)

        # Fetch details and comments for each nid
        for node_nid in all_nids:
            try:
                record = self._details_extractor.extract(
                    nid=node_nid,
                    include_related_mrs=include_related_mrs,
                    include_extra_credit=include_extra_credit,
                )
                if self._writer:
                    self._writer.write_record(record)
                if self._manifest:
                    self._manifest.increment("succeeded")
            except Exception as exc:
                url = f"https://www.drupal.org/api-d7/node/{node_nid}.json"
                if self._manifest:
                    self._manifest.record_failure(url, 0, str(exc), node_nid)

            try:
                self._comments_extractor.extract(issue_nid=node_nid, max_pages=max_pages)
            except Exception as exc:
                if self._manifest:
                    self._manifest.record_failure(
                        f"comments for {node_nid}", 0, str(exc), node_nid
                    )
