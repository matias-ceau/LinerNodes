"""Backend - Core Business Logic Layer.

This module contains the core business logic for LinerNodes, including:

- **Database**: SQLite-based storage with comprehensive schema
- **Player**: MPD integration for music playback control
- **Data Models**: Business entities (Track, Album, Artist, etc.)

## Architecture

The backend layer is designed to be interface-agnostic, providing a stable API
that can be consumed by CLI, Web, TUI, or any other interface. It handles:

### Database Management
- SQLite database with optimized schema for music metadata
- Full-text search capabilities across tracks, albums, and artists
- Source tracking for availability and synchronization
- Performance optimization with indexes and views

### Music Player Integration
- MPD (Music Player Daemon) client wrapper
- XDG-compliant configuration management
- Real-time playback status monitoring
- Playlist management and control

### Data Consistency
- Transactional operations for data integrity
- Conflict resolution for duplicate entries
- Metadata enrichment and validation
- Source synchronization tracking

## Usage

```python
from linernodes.backend.database import DatabaseManager
from linernodes.backend.player import MpdController

# Database operations
db = DatabaseManager()
tracks = db.search_music("jazz")

# Player control
player = MpdController()
player.play()
status = player.get_status()
```

## Design Principles

1. **Separation of Concerns**: Database, player, and business logic are separate
2. **Interface Independence**: Backend doesn't depend on any specific UI
3. **Data Integrity**: All operations maintain database consistency
4. **Performance**: Optimized queries and efficient data structures
5. **Extensibility**: Easy to add new data sources and player backends
"""

# Core backend imports
from .database.models import DatabaseManager, Track, Album, Artist
from .player.mpd_controller import MpdController

__all__ = [
    "DatabaseManager",
    "Track", 
    "Album",
    "Artist",
    "MpdController",
]