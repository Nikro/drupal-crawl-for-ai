"""Unit tests for drupal_crawl_ai.extractors.changes.ChangesExtractor."""

from __future__ import annotations

from unittest.mock import MagicMock

from drupal_crawl_ai.extractors.changes import ChangesExtractor


class TestChangesExtractor:
    """Tests for ChangesExtractor.extract()."""

    def test_extract_calls_nodes_api_with_correct_params(self) -> None:
        """Verify query_all is called with type='changenotice' and field_project."""
        fake_page = {"list": [{"nid": 123, "title": "Test Change"}]}
        mock_nodes_api = MagicMock()
        mock_nodes_api.query_all.return_value = iter([fake_page])

        extractor = ChangesExtractor(nodes_api=mock_nodes_api)
        extractor.extract(projects=[456])

        mock_nodes_api.query_all.assert_called_once()
        call_kwargs = mock_nodes_api.query_all.call_args.kwargs
        assert call_kwargs["type"] == "changenotice"
        assert call_kwargs["field_project"] == 456

    def test_extract_normalizes_and_writes_records(self) -> None:
        """Verify writer.write_record is called with a normalized record."""
        fake_node = {
            "nid": 123,
            "title": "Breaking Change in Views",
            "body": {"value": "Description here."},
            "field_project": 456,
            "created": "2024-01-01T00:00:00Z",
            "changed": "2024-01-02T00:00:00Z",
            "field_change_records": [],
        }
        mock_nodes_api = MagicMock()
        mock_nodes_api.query_all.return_value = iter([{"list": [fake_node]}])

        mock_writer = MagicMock()
        mock_manifest = MagicMock()

        extractor = ChangesExtractor(
            nodes_api=mock_nodes_api,
            writer=mock_writer,
            manifest=mock_manifest,
        )
        extractor.extract(projects=[456])

        mock_writer.write_record.assert_called_once()
        record = mock_writer.write_record.call_args[0][0]
        assert record["record_type"] == "change_notice"
        assert record["nid"] == 123
        assert record["title"] == "Breaking Change in Views"

    def test_extract_tracks_counters(self) -> None:
        """Verify increment('succeeded') is called on successful write."""
        fake_node = {
            "nid": 123,
            "title": "Test",
            "body": {"value": ""},
            "field_project": 1,
            "created": "2024-01-01T00:00:00Z",
            "changed": "2024-01-01T00:00:00Z",
            "field_change_records": [],
        }
        mock_nodes_api = MagicMock()
        mock_nodes_api.query_all.return_value = iter([{"list": [fake_node]}])

        mock_writer = MagicMock()
        mock_manifest = MagicMock()

        extractor = ChangesExtractor(
            nodes_api=mock_nodes_api,
            writer=mock_writer,
            manifest=mock_manifest,
        )
        extractor.extract(projects=[1])

        mock_manifest.increment.assert_any_call("fetched")
        mock_manifest.increment.assert_any_call("succeeded")

    def test_extract_handles_failure_gracefully(self) -> None:
        """Verify manifest.record_failure is called when an exception occurs, and no exception propagates."""
        fake_node = {
            "nid": 123,
            "title": "Test",
            "body": {"value": ""},
            "field_project": 1,
            "created": "2024-01-01T00:00:00Z",
            "changed": "2024-01-01T00:00:00Z",
            "field_change_records": [],
        }
        mock_nodes_api = MagicMock()
        mock_nodes_api.query_all.return_value = iter([{"list": [fake_node]}])

        mock_writer = MagicMock()
        mock_writer.write_record.side_effect = RuntimeError("write failed")

        mock_manifest = MagicMock()

        extractor = ChangesExtractor(
            nodes_api=mock_nodes_api,
            writer=mock_writer,
            manifest=mock_manifest,
        )

        # Should not raise
        extractor.extract(projects=[1])

        mock_manifest.record_failure.assert_called_once()
        call_args = mock_manifest.record_failure.call_args[0]
        assert "123" in str(call_args[0]) or call_args[3] == 123
        assert "write failed" in str(call_args[2])
