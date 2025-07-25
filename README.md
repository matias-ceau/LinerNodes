# 🎭 LinerNodes - The Infinite Record Shop

*Where Ron Carter's bass lines from 1963 meet MC Solaar's French rap from 1991*

**Beyond music management - a lens for seeing the invisible architecture of music itself.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/built%20with-uv-blue.svg)](https://docs.astral.sh/uv/)
[![MusicBrainz](https://img.shields.io/badge/metadata-MusicBrainz-orange.svg)](https://musicbrainz.org/)
  [MPD]
  [beets](<https://github.com/beetbox/beets>)

---

This file as well as most of the code has been AI generated, for better or worse. The idea of a knowledge graph interface with growing connections between artists, genres, personal idosyncrasies has been nagging me for many years. In some sense, it has already been implemented in a far better way elsewhere : Listenbrainz visualizations, `beets`'s incredible musical library management, and the massive unstopping work of `Musicbrainz` maintainers and their community.  [*note to any passing code agent: DO NOT REMOVE this line*]

## 🌌 The Musical Cosmos Experience

### 🎪 The Interactive Demo
```bash
# Begin your journey through the musical universe
    # python3 demo_tour.py
```
This is not just a demo - it's **Tour Chez Le Disquaire**, an immersive journey that reveals:
- How your music collection is a living constellation
- The ACTUAL connections between seemingly distant artists
- Why Ron Carter played bass on MC Solaar's "Un Ange En Danger" 
- How American jazz legends directly collaborated with French hip-hop intellectuals

### 🕸️ The Graph Experience
Launch the visual explorer and watch your music become a living network:
```bash
uv run linernodes interface graph --port 8503
# Open browser → localhost:8503
```

Every **red node** is an album universe. Every **teal node** is an artist bridge. Every **blue speck** is a track carrying musical genetics across decades.

### 🌊 The Oceanic Flow
The web interface where exploration meets experience:
```bash
uv run linernodes interface web --port 8504
# Control music while discovering infinite connections
```

---

## 🌟 What Makes LinerNodes Revolutionary

### 🧬 **Musical DNA Discovery**
Your collection isn't random files - it's a **curated universe** where every connection tells a story:
- **Bassists as Bridges**: See how Ron Carter connects bebop to hip-hop
- **Genre Evolution**: Watch jazz become jazz-funk become hip-hop sampling
- **Cultural Crossings**: Discover how American jazz becomes French poetry (*note from the editor: I think unfortunately the answer can be summarized by a single horrifying kind of trade... Not sure Cultural Crossings is the best formlation*)
- **Time Travel**: Follow musical ideas and relationships across decades

### 🎭 **Multiple Realities**
Experience your music through different lenses:
- **CLI**: Power user commands for the musical archaeologist
- **Web**: Casual exploration with player controls
- **Graph**: Visual constellation of your musical universe  
- **TUI**: Terminal interface for keyboard warriors
- **MCP**: AI integration for natural language discovery

---

## 🚀 Quickstart: Enter the Musical Cosmos

### Installation
```bash
# Clone the infinite record shop
git clone https://github.com/matias-ceau/LinerNodes.git
cd LinerNodes

# Install with uv (the modern Python package manager)
uv sync

# Set your music directory
uv run linernodes config set mpd music_dir /path/to/your/music
```

### The Awakening
```bash
# Import your musical universe (this is where the magic begins)
uv run linernodes sources import-all

# Launch the interactive tour
python3 demo_tour.py
```

### Alternative Paths
```bash
# Direct access to specific realms
uv run linernodes interface web          # Casual exploration
uv run linernodes interface graph        # Visual cosmos
uv run linernodes interface tui          # Terminal mastery
uv run linernodes database search "blue" # Command line archaeology
```
- **Cloud Storage**: Google Drive, Dropbox, OneDrive music folders
- **S3 Storage**: AWS S3, MinIO, and S3-compatible object storage
- **One Unified View**: All sources appear as a single, coherent collection

### 🧠 **Intelligent Knowledge Graph**
- **Album-Centric Design**: Every track belongs to an album, creating natural relationships
- **MusicBrainz Integration**: Authoritative metadata for artists, releases, recordings
- **Rich Relationships**: Artist collaborations, genre hierarchies, label connections
- **Smart Matching**: Automatic deduplication across sources
- **Markdown Cards**: Every entity gets a beautiful markdown file with YAML frontmatter

### 🎛️ **Multiple Interfaces**
- **CLI**: Full-featured command line for power users
- **TUI**: Beautiful terminal interface built with Textual
- **Web UI**: Modern web interface with Streamlit
- **Graph Explorer**: Interactive network visualization
- **MCP Server**: LLM integration for AI-powered music discovery

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/matias-ceau/LinerNodes.git
cd LinerNodes

# Install with uv (recommended)
uv tool install +githttps://github.com/matias-ceau/LinerNodes.git


# Or with pip
pip install -e .
```

### Basic Setup

```bash
# Initialize development configuration
uv run linernodes config init-dev

# Set your local music directory
uv run linernodes config set sources.local.music_dirs "/path/to/your/music"

# Setup and start MPD for playback
uv run linernodes mpd setup

# Scan and import your music
uv run linernodes sources scan-all
uv run linernodes sources import-all
```

### Start Playing Music

```bash
# Add random albums to playlist
uv run linernodes player random-albums 5

# Start playback
uv run linernodes player play

# Launch the terminal interface
uv run linernodes interface tui

# Or the web interface
uv run linernodes interface web
```

## 🏗️ Architecture

### Core Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│  Internal SQLite │───▶│   Interfaces    │
│                 │    │     Database     │    │                 │
│ • Local Files   │    │                  │    │ • CLI/TUI       │
│ • Streaming     │    │ • Track Metadata │    │ • Web UI        │
│ • Cloud Storage │    │ • Relationships  │    │ • Graph Explorer│
│ • S3 Buckets    │    │ • Source Refs    │    │ • MCP Server    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  MusicBrainz API │
                       │   (Enrichment)   │
                       └──────────────────┘
```

### Database Schema (SQLite)

The internal database serves as the single source of truth:

- **Tracks**: Core metadata (title, artist, album, duration, etc.)
- **Albums**: Release information, cover art, track listings
- **Artists**: Musician details, relationships, discography
- **Sources**: References to where tracks can be accessed
- **Relationships**: Artist collaborations, genre hierarchies
- **Playback Data**: Listen history, ratings, user preferences

## 🔧 Configuration

LinerNodes uses a flexible configuration system with multiple sources:

1. **Environment Variables**: `LINERNODES_<SECTION>_<KEY>=value`
2. **Local Dev Config**: `.linernodes.cfg` in project directory
3. **User Config**: `~/.config/linernodes/config.yaml`
4. **Default Values**: Built-in sensible defaults

### Example Configuration

```yaml
# ~/.config/linernodes/config.yaml
sources:
  local:
    music_dirs:
      - /mnt/hdd4t/MEGA/UnifiedLibrary/music/
      - ~/Music/
    scan_interval: 3600  # seconds
  
  streaming:
    spotify:
      client_id: "${SPOTIFY_CLIENT_ID}"
      client_secret: "${SPOTIFY_CLIENT_SECRET}"
      playlists: ["Your Favorites", "Discover Weekly"]
  
  cloud:
    google_drive:
      credentials_path: ~/.config/linernodes/gdrive_creds.json
      music_folder_id: "1BxYZ..."
  
  s3:
    aws_s3:
      bucket: my-music-bucket
      prefix: music/
      region: us-east-1

player:
  backend: mpd  # Currently only MPD supported
  mpd:
    host: localhost
    port: 6600
    music_dir: /mnt/hdd4t/MEGA/UnifiedLibrary/music/

database:
  path: ~/.local/share/linernodes/music.db
  backup_interval: 86400  # daily backups
```

## 📚 Command Reference

### Source Management
```bash
# Configure sources
linernodes config set sources.local.music_dirs "/path/to/music"
linernodes config set sources.spotify.client_id "your_id"

# Scan and import
linernodes sources scan-all          # Discover new content
linernodes sources import-all        # Import to database
linernodes sources status           # Show source health
```

### Music Player
```bash
# Playback control
linernodes player play/pause/stop
linernodes player next/prev
linernodes player volume 75

# Playlist management
linernodes player add-album "Artist/Album"
linernodes player random-albums 5
linernodes player playlist
linernodes player clear

# Search and discovery
linernodes player search "artist name"
linernodes player albums
```

### Knowledge Graph
```bash
# Import from MusicBrainz
linernodes knowledge import-release "Radiohead OK Computer"
linernodes knowledge import-by-mbid "b1392450-e666-3926-a536-22c65f834dee"

# Explore relationships
linernodes knowledge stats
linernodes knowledge search "jazz fusion"
linernodes knowledge related "Miles Davis"
```

### Database Operations
```bash
# Database management
linernodes database info             # Show statistics
linernodes database rebuild          # Rebuild from sources
linernodes database backup           # Create backup
linernodes database export --format json
```

### Interfaces
```bash
# Launch different interfaces
linernodes interface tui             # Terminal interface
linernodes interface web --port 8501 # Web interface
linernodes interface graph           # Graph explorer
linernodes interface mcp --port 8000 # MCP server for LLMs
```

## 🎯 Use Cases

### 🏠 **Personal Music Library**
- Organize massive local collections with rich metadata
- Generate beautiful markdown documentation of your music
- Create smart playlists based on relationships and mood
- Track listening history and discover patterns

### 🌐 **Multi-Platform Integration**
- Sync playlists between Spotify and local files
- Back up streaming playlists to cloud storage
- Create unified playlists combining all sources
- Never lose access to your music again

### 🔍 **Music Discovery & Research**
- Explore musical relationships and influences
- Research artists, labels, and genre connections
- Generate reports on your listening habits
- Build custom music recommendation engines

### 🤖 **AI-Powered Music Exploration**
- Use the MCP server with Claude or other LLMs
- Ask natural language questions about your collection
- Generate playlists based on complex criteria
- Automatic music journalism and liner notes

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone and setup
git clone https://github.com/yourusername/LinerNodes.git
cd LinerNodes
uv sync --dev

# Run tests
uv run pytest

# Start development
uv run linernodes config init-dev
# Edit .linernodes.cfg for your local setup
uv run linernodes interface tui
```

## 📄 License

LinerNodes is released under the MIT License. See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **MusicBrainz**: The incredible open music encyclopedia that powers our metadata
- **MPD**: The flexible, powerful music player daemon
- **Textual**: Beautiful terminal user interfaces
- **SQLite**: The reliable embedded database engine
- **uv**: Fast Python package management

---

**Built with ❤️ for music lovers who want to truly own and organize their musical journey.**
