"""
Base classes and interfaces for music source management.
Defines the contract that all source types must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Iterator, Optional, Tuple, Type
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class SourceTrack:
    """Represents a track discovered from a source."""
    # Required fields
    title: str
    source_type: str
    source_id: str  # Unique identifier within the source
    
    # Optional metadata
    artist: Optional[str] = None
    album: Optional[str] = None
    track_number: Optional[int] = None
    disc_number: Optional[int] = None
    duration_ms: Optional[int] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    format: Optional[str] = None
    quality: Optional[str] = None
    
    # Source-specific data
    source_url: Optional[str] = None
    source_metadata: Optional[Dict[str, Any]] = None
    
    # MusicBrainz IDs (if available)
    mbid: Optional[str] = None
    album_mbid: Optional[str] = None
    artist_mbid: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            'track_number': self.track_number,
            'disc_number': self.disc_number,
            'duration_ms': self.duration_ms,
            'genre': self.genre,
            'year': self.year,
            'format': self.format,
            'mbid': self.mbid,
            'album_mbid': self.album_mbid,
            'artist_mbid': self.artist_mbid,
        }
    
    def to_source_dict(self) -> Dict[str, Any]:
        """Convert source information to dictionary."""
        return {
            'source_type': self.source_type,
            'source_id': self.source_id,
            'source_url': self.source_url,
            'metadata': self.source_metadata or {},
            'quality': self.quality,
        }


@dataclass
class SourceStatus:
    """Status information for a source."""
    name: str
    type: str
    available: bool
    total_tracks: int = 0
    last_scanned: Optional[str] = None
    error_message: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None


class MusicSource(ABC):
    """Abstract base class for all music sources."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @property
    @abstractmethod
    def source_type(self) -> str:
        """Return the source type identifier."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the source is currently available."""
        pass
    
    @abstractmethod
    def scan_tracks(self) -> Iterator[SourceTrack]:
        """Scan the source for tracks. Yields SourceTrack objects."""
        pass
    
    @abstractmethod
    def get_track_stream_url(self, source_id: str) -> Optional[str]:
        """Get a streamable URL for a track by its source ID."""
        pass
    
    def can_play_directly(self) -> bool:
        """Whether this source can play tracks directly (e.g., local files)."""
        return False
    
    def get_status(self) -> SourceStatus:
        """Get current status of this source."""
        try:
            available = self.is_available()
            return SourceStatus(
                name=self.name,
                type=self.source_type,
                available=available,
                configuration=self._get_safe_config()
            )
        except Exception as e:
            return SourceStatus(
                name=self.name,
                type=self.source_type,
                available=False,
                error_message=str(e)
            )
    
    def _get_safe_config(self) -> Dict[str, Any]:
        """Get configuration with sensitive data removed."""
        safe_config = self.config.copy()
        # Remove common sensitive keys
        sensitive_keys = ['password', 'secret', 'token', 'key', 'credentials']
        for key in list(safe_config.keys()):
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                safe_config[key] = '***'
        return safe_config
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test connection to the source. Returns (success, error_message)."""
        try:
            return self.is_available(), None
        except Exception as e:
            return False, str(e)


class LocalSource(MusicSource):
    """Base class for local sources (files, network mounts, etc.)."""
    
    @property
    def source_type(self) -> str:
        return "local"
    
    def can_play_directly(self) -> bool:
        return True
    
    def get_track_stream_url(self, source_id: str) -> Optional[str]:
        """For local files, return file:// URL."""
        path = Path(source_id)
        if path.exists():
            return path.as_uri()
        return None


class StreamingSource(MusicSource):
    """Base class for streaming sources (Spotify, Apple Music, etc.)."""
    
    def can_play_directly(self) -> bool:
        return False  # Usually requires authentication/API calls


class CloudSource(MusicSource):
    """Base class for cloud storage sources."""
    
    def can_play_directly(self) -> bool:
        return False  # Usually requires download or streaming URL


class SourceRegistry:
    """Registry for managing different source types."""
    
    def __init__(self):
        self._source_classes: Dict[str, Type[MusicSource]] = {}
        self._sources: Dict[str, MusicSource] = {}
        self.logger = logging.getLogger(f"{__name__}.SourceRegistry")
    
    def register_source_class(self, source_type: str, source_class: type):
        """Register a source class."""
        if not issubclass(source_class, MusicSource):
            raise ValueError("Source class must inherit from MusicSource")
        
        self._source_classes[source_type] = source_class  # type: ignore[assignment]
        self.logger.info(f"Registered source type: {source_type}")
    
    def create_source(self, source_type: str, name: str, config: Dict[str, Any]) -> MusicSource:
        """Create a source instance."""
        if source_type not in self._source_classes:
            raise ValueError(f"Unknown source type: {source_type}")
        
        source_class = self._source_classes[source_type]
        source = source_class(name, config)
        self._sources[name] = source
        return source
    
    def get_source(self, name: str) -> Optional[MusicSource]:
        """Get a source by name."""
        return self._sources.get(name)
    
    def get_all_sources(self) -> List[MusicSource]:
        """Get all registered sources."""
        return list(self._sources.values())
    
    def get_available_source_types(self) -> List[str]:
        """Get all available source types."""
        return list(self._source_classes.keys())


# Global source registry
source_registry = SourceRegistry()