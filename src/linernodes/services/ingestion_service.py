"""
IngestionService: thin facade over SourceManager.

No behavior changes. Methods forward to the source manager and return dicts.
Adds light logging around calls.
"""

from __future__ import annotations

from typing import Optional, Dict

# Lightweight logging (safe import)
try:
    from linernodes.logging.setup import get_logger  # type: ignore

    _logger = get_logger("services.ingestion")
except Exception:  # pragma: no cover
    import logging as _fallback_logging

    _logger = _fallback_logging.getLogger("services.ingestion")

from linernodes.sources.source_manager import SourceManager
from linernodes.backend.database.models import DatabaseManager
from linernodes.config.config_manager import ConfigManager


class IngestionService:
    """
    Application service for ingestion operations across configured sources.

    This class wraps SourceManager to provide a stable API for higher layers.
    """

    def __init__(
        self,
        source_manager: Optional[SourceManager] = None,
        config_manager: Optional[ConfigManager] = None,
        db_manager: Optional[DatabaseManager] = None,
    ) -> None:
        if source_manager is not None:
            self._manager = source_manager
        else:
            # Share managers if provided; otherwise SourceManager will create its own
            self._manager = SourceManager(
                config_manager=config_manager,
                db_manager=db_manager,
            )
        _logger.debug(
            "IngestionService initialized", extra={"operation": "ingestion_init"}
        )

    def scan_all(self) -> Dict:
        _logger.info("scan_all invoked", extra={"operation": "ingestion_scan_all"})
        return self._manager.scan_all_sources()

    def import_all(self) -> Dict:
        _logger.info("import_all invoked", extra={"operation": "ingestion_import_all"})
        return self._manager.import_all_sources()

    def status(self) -> Dict:
        _logger.debug("status invoked", extra={"operation": "ingestion_status"})
        statuses = self._manager.get_source_statuses()
        # Normalize each status object to a plain dict without relying on to_dict
        normalized = []
        for s in statuses:
            if isinstance(s, dict):
                normalized.append(s)
            else:
                # dataclass-like or simple objects
                data = getattr(s, "__dict__", None)
                if isinstance(data, dict):
                    normalized.append(data)
                else:
                    normalized.append({"value": str(s)})
        return {"sources": normalized}

    def sync(self, name: str) -> Dict:
        _logger.info(
            "sync invoked",
            extra={"operation": "ingestion_sync", "name": name},
        )
        return self._manager.sync_source(name)
