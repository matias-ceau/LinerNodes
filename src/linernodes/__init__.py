"""LinerNodes - Album-Centric Music Knowledge Graph System.

LinerNodes is a comprehensive, modular music knowledge graph system built around 
album-centric data organization with MPD integration, multiple interfaces, and 
MusicBrainz connectivity.

## Core Architecture

### Album-Centric Design
The fundamental entity is the Album (any collection that could exist on a single 
physical medium). All other entities (artists, tracks, genres, labels, people) are 
related to and organized around these albums, creating a rich web of musical knowledge.

### Multi-Source Architecture
- **Local Files**: Direct filesystem scanning with mutagen metadata extraction
- **Streaming Services**: Future integration with Spotify, Apple Music, etc.
- **Cloud Storage**: Future support for Google Drive, S3, etc.
- **Manual Curation**: User-defined playlists and collections

### Database System
- **SQLite Backend**: Production-ready relational database for fast queries
- **Source Tracking**: Each track linked to its original source for availability
- **Metadata Enrichment**: MusicBrainz integration for canonical data
- **Performance Optimization**: Indexes and views for efficient operations

### Interface Modularity
- **CLI**: Full-featured command line interface with rich output
- **TUI**: Textual-based terminal interface for interactive browsing
- **Web**: Streamlit-based web interface with player controls
- **Graph Explorer**: Interactive network visualization of music relationships
- **MCP Server**: FastMCP server enabling LLM integration

### MPD Integration
- **XDG Compliance**: Follows XDG directory specifications
- **Auto Configuration**: Intelligent MPD setup and management
- **Player Control**: Full playback control with status monitoring
- **Playlist Management**: Dynamic playlist creation and manipulation

## Configuration System

Multi-source configuration with clear precedence:
1. Environment variables: `LINERNODES_<SECTION>_<KEY>=value`
2. Local dev config: `.linernodes.cfg` in current directory
3. Custom config: File specified by `LINERNODES_CONFIG_FILE`
4. User config: `~/.config/linernodes/config.yaml`
5. Default values

## Key Components

### Backend (`backend/`)
- **Database**: SQLite schema and ORM-like models
- **Player**: MPD controller with robust error handling

### Sources (`sources/`)
- **Base Classes**: Abstract interfaces for extensible source types
- **Local Files**: Filesystem scanner with metadata extraction
- **Source Manager**: Coordination of multiple source types

### Interfaces (`interfaces/`)
- **Multiple UIs**: CLI, TUI, Web, Graph visualization
- **Consistent API**: All interfaces share the same backend
- **Real-time Updates**: Live status monitoring and updates

### Configuration (`config/`)
- **Multi-source**: Environment, files, and defaults
- **Validation**: Type checking and constraint validation
- **XDG Compliance**: Standard directory locations

### CLI (`cli/`)
- **Rich Output**: Colored tables and progress indicators
- **Comprehensive Commands**: Database, sources, player, interfaces
- **Error Handling**: Graceful failures with helpful messages

## Installation & Usage

```bash
# Set music directory
uv run linernodes config set mpd music_dir /path/to/music

# Import music collection
uv run linernodes sources import-all

# Launch interfaces
uv run linernodes interface web      # Web UI
uv run linernodes interface tui      # Terminal UI
uv run linernodes interface graph    # Graph visualization

# Player control
uv run linernodes player play
uv run linernodes player current
```

## Data Organization

- **Entities**: Albums, Artists, Tracks, Genres, Labels, Works
- **Relationships**: Rich connections between all entities
- **Sources**: Multiple input sources with availability tracking
- **Metadata**: Comprehensive tagging with MusicBrainz enrichment
- **Cards**: Markdown export for Obsidian/knowledge management tools

## Development

The system is designed for extensibility:
- **Plugin Architecture**: Easy addition of new source types
- **Interface Independence**: Add new UIs without backend changes
- **Database Evolution**: Schema migrations and optimization
- **Configuration Flexibility**: Environment-specific settings

For detailed documentation, see individual module docstrings and 
the project's CLAUDE.md file.
"""

__version__ = "0.2.0"
__author__ = "LinerNodes Project"
__description__ = "Album-centric music knowledge graph with MPD integration"

# Core imports for common usage
from .config.config_manager import ConfigManager
from .backend.database.models import DatabaseManager, Track, Album, Artist
from .backend.player.mpd_controller import MpdController

# Version info
__all__ = [
    "__version__",
    "__author__", 
    "__description__",
    "ConfigManager",
    "DatabaseManager",
    "Track",
    "Album",
    "Artist",
    "MpdController",
]