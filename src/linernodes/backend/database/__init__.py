"""Database - SQLite-based Music Metadata Storage.

This module provides a comprehensive SQLite-based database system for storing
and managing music metadata with support for multiple sources and rich relationships.

## Database Architecture

### Core Tables
- **tracks**: Individual music tracks with metadata
- **albums**: Album/release information
- **artists**: Artist and person information  
- **sources**: Track source locations and availability
- **playlists**: User-defined collections
- **track_sources**: Many-to-many relationship for multi-source tracks

### Views and Optimization
- **track_details**: Denormalized view for fast queries
- **album_summary**: Album statistics and metadata
- **artist_summary**: Artist discographies and statistics
- Strategic indexes for search performance

### Design Features

#### Source-Agnostic Storage
Tracks can exist in multiple sources (local files, streaming, cloud) with
independent availability tracking:

```python
track = Track(title="Song", album_id=1)
track.save(db)

# Associate with multiple sources
db.add_track_source(track.id, "local:/path/to/file.mp3")
db.add_track_source(track.id, "spotify:track:123")
```

#### Metadata Enrichment
Support for rich metadata with fallback strategies:
- File-based tags (mutagen extraction)
- MusicBrainz canonical data
- User annotations and corrections

#### Performance Optimization
- Full-text search indexes
- Materialized views for common queries
- Connection pooling and prepared statements

## Data Models

### Track
Individual music recordings with comprehensive metadata:
- Basic info: title, artist, album, duration
- Technical: bitrate, format, file size
- Descriptive: genre, year, track number
- Relationships: album, artist, sources

### Album
Collections of tracks (albums, EPs, singles):
- Release information: title, artist, date
- Metadata: type, status, label, catalog number
- Relationships: tracks, artists, sources

### Artist
Musicians, bands, and music creators:
- Personal: name, sort name, disambiguation
- Biographical: dates, country, type
- Relationships: albums, tracks, collaborations

## Usage Examples

```python
# Initialize database
db_manager = DatabaseManager()

# Search operations
tracks = db_manager.search_music("jazz piano")
albums = db_manager.get_all_albums(limit=50)

# Data manipulation
track = Track(title="Blue Monk", artist_credit="Thelonious Monk")
track_id = track.save(db_manager.db)

# Complex queries
jazz_albums = db_manager.get_albums_by_genre("jazz")
artist_discography = db_manager.get_artist_albums("Miles Davis")
```

## Database Evolution

The schema supports migration and evolution:
- Version tracking for schema changes
- Backward compatibility maintenance
- Graceful handling of missing fields
- Performance monitoring and optimization
"""

from .database import LinerDatabase
from .models import DatabaseManager, Artist, Album, Track, Source

__all__ = ['LinerDatabase', 'DatabaseManager', 'Artist', 'Album', 'Track', 'Source']