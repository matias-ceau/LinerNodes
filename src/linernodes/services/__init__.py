"""
Application services scaffolding (Phase 1).

These services are thin facades over existing backend components to decouple
interfaces from adapters. No behavior changes and no wiring in CLI/Web yet.

Stability: experimental scaffolding - safe to import, no side-effects.
"""

from .playback_service import PlaybackService
from .library_service import LibraryService
from .ingestion_service import IngestionService
from .graph_service import GraphService
from .container import ServiceContainer

__all__ = [
    "PlaybackService",
    "LibraryService",
    "IngestionService",
    "GraphService",
    "ServiceContainer",
]
