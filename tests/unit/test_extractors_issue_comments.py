"""Unit tests for drupal_crawl_ai.extractors.issue_comments.IssueCommentsExtractor."""

from __future__ import annotations

from unittest.mock import MagicMock

from drupal_crawl_ai.extractors.issue_comments import IssueCommentsExtractor


class TestIssueCommentsExtractor:
    """Tests for IssueCommentsExtractor.extract()."""

    def test_extract_uses_node_param_not_nid(self) -> None:
        """Verify comments API is called with node=issue_nid parameter (not nid)."""
        fake_page = {
            "list": [
                {
                    "cid": 10,
                    "node": 123,
                    "subject": "Comment 1",
                    "comment_body": {"value": "First comment."},
                    "created": "2024-01-01T00:00:00Z",
                    "changed": "2024-01-01T00:00:00Z",
                    "name": "user1",
                    "mail": "user1@example.com",
                }
            ]
        }
        mock_comments_api = MagicMock()
        mock_comments_api.query_all.return_value = iter([fake_page])

        mock_writer = MagicMock()
        mock_manifest = MagicMock()

        extractor = IssueCommentsExtractor(
            comments_api=mock_comments_api,
            writer=mock_writer,
            manifest=mock_manifest,
        )
        extractor.extract(issue_nid=123)

        # The key assertion: query_all must be called with node=123, not nid=123
        call_kwargs = mock_comments_api.query_all.call_args.kwargs
        assert "node" in call_kwargs
        assert call_kwargs["node"] == 123
        assert "nid" not in call_kwargs

    def test_extract_writes_comment_records(self) -> None:
        """Verify write_comment and write_record are called for each comment."""
        fake_comment = {
            "cid": 20,
            "node": 456,
            "subject": "A reply",
            "comment_body": {"value": "Comment body text."},
            "created": "2024-01-01T00:00:00Z",
            "changed": "2024-01-01T00:00:00Z",
            "name": "user2",
            "mail": "user2@example.com",
        }
        mock_comments_api = MagicMock()
        mock_comments_api.query_all.return_value = iter([{"list": [fake_comment]}])

        mock_writer = MagicMock()
        mock_manifest = MagicMock()

        extractor = IssueCommentsExtractor(
            comments_api=mock_comments_api,
            writer=mock_writer,
            manifest=mock_manifest,
        )
        extractor.extract(issue_nid=456)

        mock_writer.write_comment.assert_called_once()
        mock_writer.write_record.assert_called_once()
        comment_record = mock_writer.write_comment.call_args[0][0]
        assert comment_record["cid"] == 20
        assert comment_record["record_type"] == "issue_comment"
