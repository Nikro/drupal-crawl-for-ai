"""Unit tests for project lookup."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from drupal_crawl_ai.discovery.project_lookup import resolve_project


def test_integer_identifier_returned_as_is():
    result = resolve_project(3060)
    assert result == 3060


def test_string_numeric_identifier():
    result = resolve_project("3060")
    assert result == 3060


def test_unresolved_alias_raises_when_not_found():
    with patch("drupal_crawl_ai.discovery.project_lookup.DrupalClient") as mock_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"list": []}
        mock_client.get.return_value = mock_response
        mock_class.return_value = mock_client

        with pytest.raises(ValueError, match="Cannot resolve"):
            resolve_project("nonexistent-project-alias")


def test_unresolved_alias_returns_zero_when_fallback_allowed():
    with patch("drupal_crawl_ai.discovery.project_lookup.DrupalClient") as mock_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"list": []}
        mock_client.get.return_value = mock_response
        mock_class.return_value = mock_client

        result = resolve_project("nonexistent-alias", allow_html_fallback=True)
        assert result == 0


def test_alias_resolved_via_api():
    with patch("drupal_crawl_ai.discovery.project_lookup.DrupalClient") as mock_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"list": [{"nid": 12345}]}
        mock_client.get.return_value = mock_response
        mock_class.return_value = mock_client

        result = resolve_project("my-project-alias")
        assert result == 12345
