"""
ServiceContainer: simple factory for application services.

Constructs and exposes service instances with shared ConfigManager and
DatabaseManager. Lazy initialization, no globals/singletons. No wiring to
CLI/Web in this phase.

Stability: experimental scaffolding - safe to import, no side-effects.
"""

from __future__ import annotations

from typing import Optional

# Lightweight logging (safe import)
try:
    from linernodes.logging.setup import get_logger  # type: ignore

    _logger = get_logger("services.container")
except Exception:  # pragma: no cover
    import logging as _fallback_logging

    _logger = _fallback_logging.getLogger("services.container")

from linernodes.config.config_manager import ConfigManager
from linernodes.backend.database.models import DatabaseManager
from linernodes.sources.source_manager import SourceManager

from .playback_service import PlaybackService
from .library_service import LibraryService
from .ingestion_service import IngestionService
from .graph_service import GraphService


class ServiceContainer:
    """
    Container that provides lazily-initialized service instances sharing
    foundational managers (ConfigManager, DatabaseManager).
    """

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        db_manager: Optional[DatabaseManager] = None,
    ) -> None:
        self._config = config_manager  # lazy create on first use if None
        self._db = db_manager  # lazy create on first use if None

        self._playback: Optional[PlaybackService] = None
        self._library: Optional[LibraryService] = None
        self._ingestion: Optional[IngestionService] = None
        self._graph: Optional[GraphService] = None

        _logger.debug(
            "ServiceContainer initialized", extra={"operation": "container_init"}
        )

    # Internal helpers
    def _get_config(self) -> ConfigManager:
        if self._config is None:
            _logger.debug(
                "Creating ConfigManager", extra={"operation": "container_get_config"}
            )
            self._config = ConfigManager()
        return self._config

    def _get_db(self) -> DatabaseManager:
        if self._db is None:
            _logger.debug(
                "Creating DatabaseManager", extra={"operation": "container_get_db"}
            )
            self._db = DatabaseManager()
        return self._db

    # Properties (lazy)
    @property
    def playback(self) -> PlaybackService:
        if self._playback is None:
            _logger.debug(
                "Creating PlaybackService",
                extra={"operation": "container_get_playback"},
            )
            self._playback = PlaybackService()
        return self._playback

    @property
    def library(self) -> LibraryService:
        if self._library is None:
            _logger.debug(
                "Creating LibraryService", extra={"operation": "container_get_library"}
            )
            self._library = LibraryService(db_manager=self._get_db())
        return self._library

    @property
    def ingestion(self) -> IngestionService:
        if self._ingestion is None:
            _logger.debug(
                "Creating IngestionService",
                extra={"operation": "container_get_ingestion"},
            )
            self._ingestion = IngestionService(
                source_manager=SourceManager(
                    config_manager=self._get_config(),
                    db_manager=self._get_db(),
                )
            )
        return self._ingestion

    @property
    def graph(self) -> GraphService:
        if self._graph is None:
            _logger.debug(
                "Creating GraphService", extra={"operation": "container_get_graph"}
            )
            self._graph = GraphService(db_manager=self._get_db())
        return self._graph
