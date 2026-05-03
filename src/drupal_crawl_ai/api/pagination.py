"""Pagination iterator for Drupal.org api-d7 query responses."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

# Default safety cap on number of pages
DEFAULT_MAX_PAGES = 20


def paginate(
    fetch_page: Callable[[str | None], dict[str, Any]],
    initial_url: str | None = None,
    *,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> Iterator[dict[str, Any]]:
    """
    Iterate over pages of a Drupal api-d7 list response.

    ``fetch_page`` is called with ``None`` for the first page, then with the
    ``next`` URL for each subsequent page. It must return the parsed JSON dict.

    Stops when:
    - ``next`` key is missing or falsy in the response
    - the ``list`` is empty
    - ``max_pages`` safety cap is reached

    Yields each full page dict.
    """
    page_count = 0
    next_url: str | None = initial_url

    while True:
        page_count += 1
        if page_count > max_pages:
            break

        page_data = fetch_page(next_url)
        entity_list = page_data.get("list")

        if not entity_list:
            break

        yield page_data

        next_url = page_data.get("next")
        if not next_url:
            break


def extract_next_url(page_data: dict[str, Any]) -> str | None:
    """Return the ``next`` URL from a page dict, or None if absent."""
    return page_data.get("next")
