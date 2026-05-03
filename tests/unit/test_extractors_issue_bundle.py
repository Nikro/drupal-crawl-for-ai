"""Unit tests for drupal_crawl_ai.extractors.issue_bundle.IssueBundleExtractor."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from drupal_crawl_ai.extractors.issue_bundle import IssueBundleExtractor


class TestIssueBundleExtractor:
    """Tests for IssueBundleExtractor.extract()."""

    def test_extract_collects_nids_from_projects(self) -> None:
        """Verify query_all is called for each project."""
        page1 = {"list": [{"nid": 10, "title": "Issue A", "body": {"value": ""},
                           "field_project": 1, "status": 1, "priority": 1,
                           "created": "2024-01-01T00:00:00Z", "changed": "2024-01-01T00:00:00Z",
                           "comment_count": 0}]}
        page2 = {"list": [{"nid": 20, "title": "Issue B", "body": {"value": ""},
                           "field_project": 2, "status": 1, "priority": 1,
                           "created": "2024-01-01T00:00:00Z", "changed": "2024-01-01T00:00:00Z",
                           "comment_count": 0}]}
        mock_nodes_api = MagicMock()
        mock_nodes_api.query_all.side_effect = [iter([page1]), iter([page2])]

        mock_writer = MagicMock()
        mock_manifest = MagicMock()

        with patch.object(IssueBundleExtractor, "__init__", lambda self, **kw: None):
            extractor = IssueBundleExtractor()
            extractor._nodes_api = mock_nodes_api
            extractor._writer = mock_writer
            extractor._manifest = mock_manifest
            extractor._issues_extractor = MagicMock()
            extractor._details_extractor = MagicMock()
            extractor._comments_extractor = MagicMock()
            extractor._config = MagicMock()
            extractor.extract(projects=[1, 2])

        assert mock_nodes_api.query_all.call_count == 2

    def test_extract_fetches_details_for_each_nid(self) -> None:
        """Verify IssueDetailsExtractor.extract is called once per discovered nid."""
        page = {"list": [
            {"nid": 5, "title": "Issue 5", "body": {"value": ""},
             "field_project": 1, "status": 1, "priority": 1,
             "created": "2024-01-01T00:00:00Z", "changed": "2024-01-01T00:00:00Z",
             "comment_count": 0},
            {"nid": 6, "title": "Issue 6", "body": {"value": ""},
             "field_project": 1, "status": 1, "priority": 1,
             "created": "2024-01-01T00:00:00Z", "changed": "2024-01-01T00:00:00Z",
             "comment_count": 0},
        ]}
        mock_nodes_api = MagicMock()
        mock_nodes_api.query_all.return_value = iter([page])

        mock_details_extractor = MagicMock()
        mock_details_extractor.extract.return_value = {"nid": 5, "record_type": "project_issue"}

        mock_comments_extractor = MagicMock()
        mock_writer = MagicMock()
        mock_manifest = MagicMock()

        with patch.object(IssueBundleExtractor, "__init__", lambda self, **kw: None):
            extractor = IssueBundleExtractor()
            extractor._nodes_api = mock_nodes_api
            extractor._writer = mock_writer
            extractor._manifest = mock_manifest
            extractor._issues_extractor = MagicMock()
            extractor._details_extractor = mock_details_extractor
            extractor._comments_extractor = mock_comments_extractor
            extractor._config = MagicMock()
            extractor.extract(projects=[1])

        assert mock_details_extractor.extract.call_count == 2
        nids_called = {
            call.kwargs["nid"]
            for call in mock_details_extractor.extract.call_args_list
        }
        assert nids_called == {5, 6}

    def test_extract_fetches_comments_for_each_nid(self) -> None:
        """Verify IssueCommentsExtractor.extract is called once per discovered nid."""
        page = {"list": [
            {"nid": 7, "title": "Issue 7", "body": {"value": ""},
             "field_project": 1, "status": 1, "priority": 1,
             "created": "2024-01-01T00:00:00Z", "changed": "2024-01-01T00:00:00Z",
             "comment_count": 0},
            {"nid": 8, "title": "Issue 8", "body": {"value": ""},
             "field_project": 1, "status": 1, "priority": 1,
             "created": "2024-01-01T00:00:00Z", "changed": "2024-01-01T00:00:00Z",
             "comment_count": 0},
        ]}
        mock_nodes_api = MagicMock()
        mock_nodes_api.query_all.return_value = iter([page])

        mock_details_extractor = MagicMock()
        mock_details_extractor.extract.return_value = {"nid": 7, "record_type": "project_issue"}

        mock_comments_extractor = MagicMock()
        mock_writer = MagicMock()
        mock_manifest = MagicMock()

        with patch.object(IssueBundleExtractor, "__init__", lambda self, **kw: None):
            extractor = IssueBundleExtractor()
            extractor._nodes_api = mock_nodes_api
            extractor._writer = mock_writer
            extractor._manifest = mock_manifest
            extractor._issues_extractor = MagicMock()
            extractor._details_extractor = mock_details_extractor
            extractor._comments_extractor = mock_comments_extractor
            extractor._config = MagicMock()
            extractor.extract(projects=[1])

        assert mock_comments_extractor.extract.call_count == 2
        issue_nids = {
            call.kwargs["issue_nid"]
            for call in mock_comments_extractor.extract.call_args_list
        }
        assert issue_nids == {7, 8}

    def test_bundle_skips_duplicates(self) -> None:
        """Verify the same nid from two projects is only processed once."""
        page1 = {"list": [
            {"nid": 99, "title": "Issue 99", "body": {"value": ""},
             "field_project": 1, "status": 1, "priority": 1,
             "created": "2024-01-01T00:00:00Z", "changed": "2024-01-01T00:00:00Z",
             "comment_count": 0}
        ]}
        page2 = {"list": [
            {"nid": 99, "title": "Issue 99 again", "body": {"value": ""},
             "field_project": 2, "status": 1, "priority": 1,
             "created": "2024-01-01T00:00:00Z", "changed": "2024-01-01T00:00:00Z",
             "comment_count": 0}
        ]}
        mock_nodes_api = MagicMock()
        mock_nodes_api.query_all.side_effect = [iter([page1]), iter([page2])]

        mock_details_extractor = MagicMock()
        mock_details_extractor.extract.return_value = {"nid": 99, "record_type": "project_issue"}

        mock_comments_extractor = MagicMock()
        mock_writer = MagicMock()
        mock_manifest = MagicMock()

        with patch.object(IssueBundleExtractor, "__init__", lambda self, **kw: None):
            extractor = IssueBundleExtractor()
            extractor._nodes_api = mock_nodes_api
            extractor._writer = mock_writer
            extractor._manifest = mock_manifest
            extractor._issues_extractor = MagicMock()
            extractor._details_extractor = mock_details_extractor
            extractor._comments_extractor = mock_comments_extractor
            extractor._config = MagicMock()
            extractor.extract(projects=[1, 2])

        # nid 99 appears in both projects but details/comments should only be fetched once
        assert mock_details_extractor.extract.call_count == 1
        assert mock_comments_extractor.extract.call_count == 1
