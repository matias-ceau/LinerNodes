"""LinerNodes music source management system."""

from .base import MusicSource, SourceTrack, SourceStatus, source_registry
from .source_manager import SourceManager

# Import source implementations to register them
from . import local_files

__all__ = ['MusicSource', 'SourceTrack', 'SourceStatus', 'source_registry', 'SourceManager']