"""
LibraryService: thin facade over DatabaseManager.

No behavior changes. Methods forward to the database manager and return results.
Export is intentionally side-effect free in this phase and returns counts only.
"""

from __future__ import annotations

from typing import List, Optional

# Lightweight logging (safe import)
try:
    from linernodes.logging.setup import get_logger  # type: ignore

    _logger = get_logger("services.library")
except Exception:  # pragma: no cover
    import logging as _fallback_logging

    _logger = _fallback_logging.getLogger("services.library")

from linernodes.backend.database.models import DatabaseManager, Track, Album


class LibraryService:
    """
    Application service for read-only library queries and simple aggregations.

    This class wraps DatabaseManager to provide a stable API for higher layers.
    It intentionally avoids any additional side-effects in this phase.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        self._db = db_manager or DatabaseManager()
        _logger.debug("LibraryService initialized", extra={"operation": "library_init"})

    def search_tracks(self, query: str, limit: int = 50) -> List[Track]:
        _logger.debug(
            "search_tracks called",
            extra={
                "operation": "library_search_tracks",
                "query": query,
                "limit": limit,
            },
        )
        return self._db.search_music(query, limit)

    def list_albums(self, limit: int = 100) -> List[Album]:
        _logger.debug(
            "list_albums called",
            extra={"operation": "library_list_albums", "limit": limit},
        )
        return self._db.get_all_albums(limit)

    def unique_artists(self, limit: int = 100) -> List[str]:
        _logger.debug(
            "unique_artists called",
            extra={"operation": "library_unique_artists", "limit": limit},
        )
        return self._db.get_unique_artists(limit)

    def export(self, format: str, path: str) -> int:
        """
        Placeholder export: return the number of items that would be exported.

        This method is intentionally side-effect free in Phase 1. Actual file
        writing should be implemented in the CLI/Web layer.

        TODO: In future phases, implement file export in the adapter layer.
        """
        _logger.debug(
            "export called (placeholder)",
            extra={"operation": "library_export", "format": format, "path": path},
        )

        # For now, approximate by counting albums to "export"
        items = self._db.get_all_albums(100000)
        return len(items)
