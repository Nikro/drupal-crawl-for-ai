"""Unit tests for DrupalClient."""

from unittest.mock import MagicMock, patch

import pytest
import requests
from drupal_crawl_ai.config import Config
from drupal_crawl_ai.http.client import DrupalClient


@pytest.fixture
def client() -> DrupalClient:
    return DrupalClient(Config())


def test_client_has_required_headers(client: DrupalClient) -> None:
    assert "Accept" in client._session.headers
    assert "User-Agent" in client._session.headers
    assert client._session.headers["Accept"] == "application/json"
    assert "drupal-crawl-for-ai" in client._session.headers["User-Agent"]


def test_delay_hook_is_invoked(client: DrupalClient) -> None:
    with patch("drupal_crawl_ai.http.client.time.sleep") as mock_sleep:
        with patch("requests.Session.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            client.get("/node.json", params={"type": "project_issue"})

            # First call should sleep delay_seconds, subsequent retries sleep longer
            assert mock_sleep.call_count >= 1


def test_delay_seconds_from_config() -> None:
    cfg = Config()
    cfg.http.delay_seconds = 0.5
    client = DrupalClient(cfg)

    with patch("drupal_crawl_ai.http.client.time.sleep") as mock_sleep:
        with patch("requests.Session.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            client.get("/node.json")

            # Verify sleep was called with approx 0.5s
            for call in mock_sleep.call_args_list:
                assert call[0][0] <= 0.6  # jitter can add up to 50%


def test_raises_on_client_error_after_max_retries() -> None:
    cfg = Config()
    cfg.http.max_retries = 2
    client = DrupalClient(cfg)

    with patch("requests.Session.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Not Found"
        )

        with pytest.raises(requests.exceptions.HTTPError):
            client.get("/node.json")
