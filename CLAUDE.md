# LinerNodes - Universal Music Knowledge Graph & Management System

A comprehensive, modular music knowledge graph system designed to unify music from any source (local files, streaming platforms, cloud storage, S3) into a single, intelligent database with rich metadata from MusicBrainz.

## Core Philosophy & Vision

**Album-Centric Knowledge Graph**: The fundamental entity is the **Album** (any collection that could exist on a single physical medium). All other entities (artists, tracks, genres, labels, people) are related to and organized around these albums, creating a rich web of musical knowledge.

**Universal Music Management**: LinerNodes serves as an authoritative, internal database that can:
- Import and manage music from multiple sources (local files, streaming APIs, cloud storage, S3 buckets)
- Maintain consistent, high-quality metadata using MusicBrainz as the authoritative reference
- Provide backend-agnostic playback (currently MPD, extensible to other players)
- Generate comprehensive knowledge graphs connecting musical relationships
- Export data to various formats (markdown cards, structured data, graph visualizations)

**Source-Agnostic Design**: Whether your music lives on local drives, Spotify playlists, Google Drive, AWS S3, or anywhere else, LinerNodes creates a unified view with consistent metadata and relationships.

## Project Structure

### Core Database & Knowledge Graph
- `src/linernodes/knowledge_graph/models.py` - Entity models (Album, Artist, Genre, Person, etc.)
- `src/linernodes/knowledge_graph/graph_db.py` - SQLite-based internal database with relationships
- `src/linernodes/knowledge_graph/markdown_cards.py` - YAML-frontmatter markdown card generation
- `src/linernodes/knowledge_graph/musicbrainz_integration.py` - MusicBrainz metadata enrichment

### Multi-Source Music Management
- `src/linernodes/sources/local_files.py` - Local file system scanning and import
- `src/linernodes/sources/streaming_apis.py` - Spotify, Apple Music, YouTube Music integration
- `src/linernodes/sources/cloud_storage.py` - Google Drive, Dropbox, OneDrive support
- `src/linernodes/sources/s3_storage.py` - AWS S3, MinIO, and S3-compatible storage
- `src/linernodes/sources/source_manager.py` - Unified source management and synchronization

### Backend Services (Playback-Agnostic)
- `src/linernodes/backend/player/mpd_controller.py` - MPD integration (current default)
- `src/linernodes/backend/player/player_interface.py` - Abstract player interface for extensibility
- `src/linernodes/backend/database/` - Internal SQLite database management
- `src/linernodes/config/config_manager.py` - Multi-source configuration management

### Modular Interfaces
- **CLI**: Full-featured command line interface (`src/linernodes/cli/commands.py`)
- **TUI**: Textual-based terminal interface (`src/linernodes/interfaces/tui.py`)
- **Web**: Streamlit-based web interface (`src/linernodes/interfaces/web.py`)  
- **Graph Explorer**: Obsidian-like graph visualization (`src/linernodes/interfaces/graph_explorer.py`)
- **MCP Server**: FastMCP server for LLM integration (`src/linernodes/interfaces/mcp_server.py`)

## Architecture & Data Flow

### Internal Database (SQLite)
LinerNodes maintains its own authoritative music database that serves as the single source of truth for:
- **Track Metadata**: Title, artist, album, duration, genre, year, etc.
- **Source References**: Where each track can be accessed (local file, streaming URL, cloud path)
- **Relationships**: Artist collaborations, album connections, genre hierarchies
- **MusicBrainz IDs**: Links to authoritative metadata for enrichment and disambiguation
- **Playback History**: Listen counts, last played, user ratings
- **Custom Tags**: User-defined labels, playlists, collections

### Multi-Source Integration
1. **Source Discovery**: Scan configured sources (local dirs, API endpoints, cloud storage)
2. **Metadata Extraction**: Extract basic metadata from each source
3. **MusicBrainz Enrichment**: Match tracks to MusicBrainz for canonical metadata
4. **Database Storage**: Store enriched metadata with source references
5. **Conflict Resolution**: Handle duplicates across sources intelligently
6. **Synchronization**: Keep sources in sync with database state

## Configuration System

**Multi-Source Configuration** with precedence (highest to lowest):
1. **Environment variables**: `LINERNODES_<SECTION>_<KEY>=value`
2. **Local dev config**: `.linernodes.cfg` in current directory  
3. **Custom config**: File specified by `LINERNODES_CONFIG_FILE`
4. **User config**: `~/.config/linernodes/config.yaml`
5. **Default values**

### Example Configuration Sources
```yaml
sources:
  local:
    music_dirs:
      - /mnt/hdd4t/MEGA/UnifiedLibrary/music/
      - ~/Music/
  streaming:
    spotify:
      client_id: ${SPOTIFY_CLIENT_ID}
      client_secret: ${SPOTIFY_CLIENT_SECRET}
  cloud:
    google_drive:
      credentials_path: ~/.config/linernodes/gdrive_creds.json
      music_folder_id: "1BxYZ..."
  s3:
    aws_s3:
      bucket: my-music-bucket
      prefix: music/
      region: us-east-1
```

### Configuration Commands
- `uv run linernodes config info` - Show config sources and precedence
- `uv run linernodes config init-dev` - Create development config template
- `uv run linernodes config get [section] [key]` - View configuration
- `uv run linernodes config set <section> <key> <value>` - Set configuration
- `uv run linernodes config validate` - Validate current configuration

## Music Sources & Knowledge Graph

### Multi-Source Setup
```bash
# Configure local music directories
uv run linernodes config set sources.local.music_dirs "/mnt/music,~/Music"

# Add streaming service credentials
uv run linernodes config set sources.streaming.spotify.client_id "your_client_id"

# Configure cloud storage
uv run linernodes config set sources.cloud.google_drive.credentials_path "~/.config/creds.json"

# Add S3-compatible storage
uv run linernodes config set sources.s3.aws_s3.bucket "music-bucket"

# Discover and import from all sources
uv run linernodes sources scan-all
uv run linernodes sources import-all

# Import specific albums with MusicBrainz enrichment
uv run linernodes knowledge import-release "artist album name"
uv run linernodes knowledge import-by-mbid <musicbrainz-id>

# View knowledge graph statistics
uv run linernodes knowledge stats

# Search across all sources
uv run linernodes knowledge search "query"
```

### Database Management
```bash
# View database statistics
uv run linernodes database info

# Rebuild internal database from sources
uv run linernodes database rebuild

# Export database to various formats
uv run linernodes database export --format json
uv run linernodes database export --format csv
uv run linernodes database export --format markdown
```

### Entity Types & Relationships
- **Album**: Central entity (release/physical medium equivalent)
- **Artist/Person**: Musicians, producers, engineers
- **Genre**: Musical styles with hierarchical relationships
- **Recording**: Individual tracks/songs
- **Label**: Record labels and publishers
- **Work**: Compositions and musical works

### Markdown Cards
Every entity automatically generates a markdown card with YAML frontmatter:
- Stored in `~/.local/share/linernodes/cards/`
- Organized by entity type (`album/`, `artist/`, `genre/`, etc.)
- Contains full metadata, relationships, and entity-specific information
- Compatible with Obsidian and other markdown-based knowledge tools

## Interface Commands

### Player Control
- `uv run linernodes player play` - Start/resume playback
- `uv run linernodes player pause` - Pause playback  
- `uv run linernodes player stop` - Stop playback
- `uv run linernodes player next` - Skip to next track
- `uv run linernodes player prev` - Skip to previous track
- `uv run linernodes player volume <0-100>` - Set volume level
- `uv run linernodes player current` - Show detailed current track info
- `uv run linernodes player playlist` - Show current playlist
- `uv run linernodes player add <file>` - Add track to playlist
- `uv run linernodes player clear` - Clear current playlist

### MPD Management  
- `uv run linernodes mpd setup` - Configure and setup MPD
- `uv run linernodes mpd status` - Check MPD status

### Interface Launchers
- `uv run linernodes interface tui` - Terminal interface
- `uv run linernodes interface web [--port 8501]` - Web interface  
- `uv run linernodes interface graph [--port 8502]` - Graph explorer (Obsidian-like)
- `uv run linernodes interface mcp [--host 0.0.0.0] [--port 8000]` - MCP server

## Development

### Quick Start
```bash
# Create development config
uv run linernodes config init-dev

# Edit .linernodes.cfg for local settings
# Set environment overrides
export LINERNODES_MPD_MUSIC_DIR=/path/to/test/music

# Run tests
uv run pytest

# Launch development interface
uv run linernodes interface graph
```

### Architecture Benefits

- **Knowledge Graph**: Rich, interconnected musical metadata beyond simple file tags
- **Album-Centric**: Organized around the fundamental unit of music releases
- **Modular Design**: Independent interfaces sharing the same knowledge core
- **Multi-Source Config**: Flexible configuration for different environments
- **MusicBrainz Integration**: Automatic import of high-quality, standardized metadata  
- **LLM Integration**: MCP server enables AI tool access to musical knowledge
- **Markdown Export**: All entities available as structured markdown files
- **Graph Visualization**: Explore your collection as an interconnected web of relationships

## Memories
- Reference for metadata is MusicBrainz

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.