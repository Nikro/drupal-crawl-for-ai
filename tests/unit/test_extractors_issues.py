"""Unit tests for drupal_crawl_ai.extractors.issues.IssuesExtractor."""

from __future__ import annotations

from unittest.mock import MagicMock

from drupal_crawl_ai.extractors.issues import IssuesExtractor


class TestIssuesExtractor:
    """Tests for IssuesExtractor.extract()."""

    def test_extract_uses_project_issue_type(self) -> None:
        """Verify query_all is called with type='project_issue'."""
        mock_nodes_api = MagicMock()
        mock_nodes_api.query_all.return_value = iter([{"list": []}])

        extractor = IssuesExtractor(nodes_api=mock_nodes_api)
        extractor.extract(projects=[123])

        call_kwargs = mock_nodes_api.query_all.call_args.kwargs
        assert call_kwargs["type"] == "project_issue"
        assert call_kwargs["field_project"] == 123

    def test_extract_respects_max_issues(self) -> None:
        """Verify only max_issues records are written when limit is set."""
        nodes = [
            {"nid": i, "title": f"Issue {i}", "body": {"value": ""},
             "field_project": 1, "status": 1, "priority": 1,
             "created": "2024-01-01T00:00:00Z", "changed": "2024-01-01T00:00:00Z",
             "comment_count": 0}
            for i in range(1, 6)
        ]
        mock_nodes_api = MagicMock()
        mock_nodes_api.query_all.return_value = iter([{"list": nodes}])

        mock_writer = MagicMock()
        mock_manifest = MagicMock()

        extractor = IssuesExtractor(
            nodes_api=mock_nodes_api,
            writer=mock_writer,
            manifest=mock_manifest,
        )
        extractor.extract(projects=[1], max_issues=3)

        assert mock_writer.write_record.call_count == 3

    def test_extract_deduplicates_by_nid(self) -> None:
        """Verify the same nid appearing in two pages is only written once."""
        page1 = {
            "list": [
                {"nid": 1, "title": "Issue 1", "body": {"value": ""},
                 "field_project": 1, "status": 1, "priority": 1,
                 "created": "2024-01-01T00:00:00Z", "changed": "2024-01-01T00:00:00Z",
                 "comment_count": 0}
            ]
        }
        page2 = {
            "list": [
                {"nid": 1, "title": "Issue 1 (dup)", "body": {"value": ""},
                 "field_project": 1, "status": 1, "priority": 1,
                 "created": "2024-01-01T00:00:00Z", "changed": "2024-01-01T00:00:00Z",
                 "comment_count": 0},
                {"nid": 2, "title": "Issue 2", "body": {"value": ""},
                 "field_project": 1, "status": 1, "priority": 1,
                 "created": "2024-01-01T00:00:00Z", "changed": "2024-01-01T00:00:00Z",
                 "comment_count": 0}
            ]
        }
        mock_nodes_api = MagicMock()
        mock_nodes_api.query_all.return_value = iter([page1, page2])

        mock_writer = MagicMock()
        mock_manifest = MagicMock()

        extractor = IssuesExtractor(
            nodes_api=mock_nodes_api,
            writer=mock_writer,
            manifest=mock_manifest,
        )
        extractor.extract(projects=[1])

        # nid=1 should only be written once; nid=2 should be written once = 2 total
        assert mock_writer.write_record.call_count == 2
        nids_written = [
            call[0][0]["nid"]
            for call in mock_writer.write_record.call_args_list
        ]
        assert nids_written.count(1) == 1
        assert 2 in nids_written

    def test_extract_tracks_counters(self) -> None:
        """Verify increment('succeeded') is called on successful write."""
        fake_node = {
            "nid": 1, "title": "Issue 1", "body": {"value": ""},
            "field_project": 1, "status": 1, "priority": 1,
            "created": "2024-01-01T00:00:00Z", "changed": "2024-01-01T00:00:00Z",
            "comment_count": 0
        }
        mock_nodes_api = MagicMock()
        mock_nodes_api.query_all.return_value = iter([{"list": [fake_node]}])

        mock_writer = MagicMock()
        mock_manifest = MagicMock()

        extractor = IssuesExtractor(
            nodes_api=mock_nodes_api,
            writer=mock_writer,
            manifest=mock_manifest,
        )
        extractor.extract(projects=[1])

        mock_manifest.increment.assert_any_call("fetched")
        mock_manifest.increment.assert_any_call("succeeded")
