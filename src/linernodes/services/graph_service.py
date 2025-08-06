"""
GraphService: thin facade for knowledge graph data retrieval.

Default behavior uses DatabaseManager.get_graph_data_bulk_cached(limit).
Provides cache invalidation method.

TODO: Consider enabling a DuckDB backend via a feature flag in a future phase.
"""

from __future__ import annotations

from typing import Optional, Dict, Any

# Lightweight logging (safe import)
try:
    from linernodes.logging.setup import get_logger  # type: ignore

    _logger = get_logger("services.graph")
except Exception:  # pragma: no cover
    import logging as _fallback_logging

    _logger = _fallback_logging.getLogger("services.graph")

from linernodes.backend.database.models import DatabaseManager


class GraphService:
    """
    Application service for graph data access.

    This class wraps DatabaseManager graph APIs to provide a stable interface.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        self._db = db_manager or DatabaseManager()
        _logger.debug("GraphService initialized", extra={"operation": "graph_init"})

    def graph_data(self, limit: int = 5000) -> Dict[str, Any]:
        _logger.debug(
            "graph_data called",
            extra={"operation": "graph_data", "limit": limit},
        )
        return self._db.get_graph_data_bulk_cached(limit)

    def invalidate_cache(self) -> None:
        _logger.info("invalidate_cache called", extra={"operation": "graph_invalidate"})
        self._db.invalidate_graph_cache()
