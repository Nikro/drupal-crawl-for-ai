"""Polite HTTP client with session, headers, pacing, timeout, and retry/backoff."""

from __future__ import annotations

import random
import time
from typing import Any

import requests
from requests import Response

from drupal_crawl_ai.config import Config, HttpConfig

# HTTP statuses that trigger a retry
_RETRY_ON_STATUS = {429, 500, 501, 502, 503, 504, 599}

# Statuses that indicate a client error — never retry
_NO_RETRY_ON_STATUS = {400, 401, 403, 404, 410, 422}


def _jitter(backoff: float) -> float:
    """Add uniform random jitter to a backoff value."""
    return backoff * (0.5 + random.random())


class DrupalClient:
    """Polite, single-threaded HTTP client for Drupal.org API endpoints."""

    def __init__(self, config: Config | None = None) -> None:
        self._config = config or Config()
        self._http: HttpConfig = self._config.http
        self._session = requests.Session()
        self._session.headers.update({
            "Accept": self._http.accept_header,
            "User-Agent": self._http.user_agent,
        })

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        _attempt: int = 0,
    ) -> Response:
        """
        Fetch a GET request with polite pacing, timeout, and retry/backoff.

        params are sorted before building the URL to ensure deterministic cache keys.
        """
        # Sort params for deterministic request identity
        sorted_params: dict[str, Any] | None
        if params:
            sorted_params = dict(sorted(params.items()))
        else:
            sorted_params = None

        # Accept both absolute URLs (from Drupal's "next") and relative
        # paths (our own API calls). Skip join if path is already absolute.
        if path.startswith("http://") or path.startswith("https://"):
            url = path
        else:
            url = f"{self._http.base_url}/{path.lstrip('/')}"

        # Pre-request pacing delay (after first attempt)
        if _attempt > 0:
            sleep_time = _jitter(self._http.delay_seconds * (2 ** (_attempt - 1)))
            time.sleep(sleep_time)
        else:
            time.sleep(self._http.delay_seconds)

        response = self._session.get(
            url,
            params=sorted_params,
            timeout=self._http.timeout_seconds,
        )

        # Retry logic
        if response.status_code in _RETRY_ON_STATUS and _attempt < self._http.max_retries:
            return self.get(path, sorted_params, _attempt=_attempt + 1)

        # Always raise for error statuses that were not retried
        response.raise_for_status()
        return response

    def close(self) -> None:
        self._session.close()
