"""Unit tests for drupal_crawl_ai.extractors.issue_details.IssueDetailsExtractor."""

from __future__ import annotations

from unittest.mock import MagicMock

from drupal_crawl_ai.extractors.issue_details import IssueDetailsExtractor


class TestIssueDetailsExtractor:
    """Tests for IssueDetailsExtractor.extract()."""

    def test_extract_fetches_correct_nid(self) -> None:
        """Verify get_node is called with the correct nid."""
        mock_nodes_api = MagicMock()
        mock_nodes_api.get_node.return_value = {
            "nid": 123,
            "title": "Test Issue",
            "body": {"value": "Issue body."},
            "field_project": 1,
            "status": 1,
            "priority": 1,
            "created": "2024-01-01T00:00:00Z",
            "changed": "2024-01-01T00:00:00Z",
            "comment_count": 0,
        }

        extractor = IssueDetailsExtractor(nodes_api=mock_nodes_api)
        extractor.extract(nid=123)

        mock_nodes_api.get_node.assert_called_once_with(123)

    def test_extract_returns_normalized_record(self) -> None:
        """Verify extract returns a properly normalized record."""
        fake_node = {
            "nid": 456,
            "title": "My Issue",
            "body": {"value": "Issue description."},
            "field_project": 10,
            "status": 1,
            "priority": 2,
            "created": "2024-02-01T00:00:00Z",
            "changed": "2024-02-02T00:00:00Z",
            "comment_count": 5,
        }
        mock_nodes_api = MagicMock()
        mock_nodes_api.get_node.return_value = fake_node

        extractor = IssueDetailsExtractor(nodes_api=mock_nodes_api)
        record = extractor.extract(nid=456)

        assert record["record_type"] == "project_issue"
        assert record["nid"] == 456
        assert record["title"] == "My Issue"
        assert "fetched_at" in record
        assert "source_url" in record
