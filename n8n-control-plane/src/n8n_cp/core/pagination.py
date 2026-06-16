"""Pagination + data-volume guards.

The n8n Public API is cursor-based: list responses carry ``data`` and
``nextCursor``. We never fetch unbounded amounts: a per-page default and a hard
ceiling per agent operation protect the instance and the agent's context.
"""
from __future__ import annotations

from typing import Any, Callable, Iterator, Optional

DEFAULT_LIMIT = 100
MAX_ITEMS_PER_OPERATION = 10_000


def clamp_limit(limit: Optional[int]) -> int:
    if not limit or limit < 1:
        return DEFAULT_LIMIT
    return min(limit, 250)  # n8n per-page max


def iterate(fetch_page: Callable[[Optional[str]], dict],
            max_items: int = MAX_ITEMS_PER_OPERATION) -> Iterator[dict]:
    """Yield items across pages, stopping at ``max_items`` or when the cursor
    runs out. ``fetch_page(cursor)`` must return a dict with ``data`` (list) and
    optional ``nextCursor``."""
    cursor: Optional[str] = None
    seen = 0
    while True:
        page = fetch_page(cursor)
        items = page.get("data", []) or []
        for item in items:
            yield item
            seen += 1
            if seen >= max_items:
                return
        cursor = page.get("nextCursor")
        if not cursor:
            return


def collect(fetch_page: Callable[[Optional[str]], dict],
            max_items: int = MAX_ITEMS_PER_OPERATION) -> tuple[list, Optional[str], bool]:
    """Collect up to ``max_items`` items. Returns (items, next_cursor, truncated).

    ``truncated`` is True if we hit the ceiling before exhausting the cursor."""
    items: list[Any] = []
    cursor: Optional[str] = None
    truncated = False
    while True:
        page = fetch_page(cursor)
        batch = page.get("data", []) or []
        for item in batch:
            items.append(item)
            if len(items) >= max_items:
                return items, page.get("nextCursor"), True
        cursor = page.get("nextCursor")
        if not cursor:
            break
    return items, None, truncated
