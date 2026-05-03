"""Per-entity markdown file writer."""

from __future__ import annotations

from pathlib import Path


class MarkdownWriter:
    """
    Per-entity markdown file writer.

    Path convention: <root>/<record_type>/<entity_id>.md
    """

    def __init__(self, root: Path) -> None:
        self._root = root

    def write(self, record_type: str, entity_id: int | str, content: str) -> Path:
        """
        Write ``content`` to the markdown file for this entity.

        Creates parent directories as needed. Returns the Path written to.
        Overwrite is allowed (idempotent).
        """
        path = self._root / record_type / f"{entity_id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path
