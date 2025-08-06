"""
Service Protocols (lightweight facades)

These Protocols describe the minimal API surface for application services that
wrap existing backend components. They intentionally avoid importing heavy
modules at runtime to prevent circular imports. Concrete services live in this
package and forward to backend implementations without changing behavior.

Stability: experimental scaffolding - safe to import, no side-effects.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable, List, Dict, Optional, TYPE_CHECKING

# Import entity types only for typing (avoid runtime imports/circulars)
if TYPE_CHECKING:  # pragma: no cover
    from linernodes.backend.database.models import Track, Album  # noqa: F401


@runtime_checkable
class PlaybackServiceProto(Protocol):
    """
    Protocol for playback operations wrapping MPD or other playback engines.
    """

    def play(self, pos: Optional[int] = None) -> None: ...
    def pause(self) -> None: ...
    def stop(self) -> None: ...
    def next(self) -> None: ...
    def previous(self) -> None: ...
    def set_volume(self, volume: int) -> None: ...
    def status(self) -> Dict: ...
    def playlist(self) -> List[Dict]: ...
    def add_file(self, path: str) -> None: ...
    def add_album(self, album_path: str) -> List[str]: ...
    def load_random_albums(self, count: int) -> List[str]: ...


@runtime_checkable
class LibraryServiceProto(Protocol):
    """
    Protocol for library queries and lightweight export calculations.
    """

    def search_tracks(self, query: str, limit: int) -> List["Track"]: ...
    def list_albums(self, limit: int) -> List["Album"]: ...
    def unique_artists(self, limit: int) -> List[str]: ...
    def export(self, format: str, path: str) -> int: ...


@runtime_checkable
class IngestionServiceProto(Protocol):
    """
    Protocol for ingestion operations over configured Sources.
    """

    def scan_all(self) -> Dict: ...
    def import_all(self) -> Dict: ...
    def status(self) -> Dict: ...
    def sync(self, name: str) -> Dict: ...


@runtime_checkable
class GraphServiceProto(Protocol):
    """
    Protocol for knowledge graph data access.
    """

    def graph_data(self, limit: int) -> Dict: ...
    def invalidate_cache(self) -> None: ...
