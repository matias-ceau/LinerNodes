"""Interfaces - Multiple User Interface Implementations.

This module provides various user interfaces for interacting with the LinerNodes
music system, each optimized for different use cases and environments.

## Available Interfaces

### Command Line Interface (CLI)
Full-featured command-line interface with rich formatting:
- **Database Management**: Search, import, export, optimization
- **Source Management**: Scan, import, synchronization
- **Player Control**: Play, pause, stop, volume, playlist management
- **Configuration**: View, set, validate configuration
- **Interface Launchers**: Start web, TUI, or graph interfaces

### Web Interface (`web.py`)
Streamlit-based web interface for browser access:
- **Real-time Player Control**: Play/pause/stop/next/previous
- **Music Library Browsing**: Search tracks, albums, artists
- **Playlist Management**: Add tracks, view current playlist
- **Volume Control**: Interactive volume slider
- **Live Status**: Auto-refreshing player status

### Terminal User Interface (`tui.py`)
Textual-based interactive terminal interface:
- **Keyboard Navigation**: Vim-like key bindings
- **Library Browser**: Hierarchical music collection browsing
- **Player Dashboard**: Current track info and controls
- **Search Interface**: Real-time search with filtering
- **Playlist Editor**: Interactive playlist management

### Graph Explorer (`graph_explorer.py`)
Interactive network visualization of music relationships:
- **Knowledge Graph**: Visual representation of music connections
- **Entity Relationships**: Artists, albums, tracks, genres
- **Interactive Exploration**: Click, zoom, pan through network
- **Search and Filter**: Find entities and highlight connections
- **Network Analysis**: Discover patterns in music collection

### MCP Server (`mcp_server.py`)
FastMCP server for LLM integration:
- **AI Tool Access**: Expose music operations to language models
- **Natural Language Queries**: Search music using conversational interface
- **Automated Operations**: LLM-driven playlist creation and management
- **Context Integration**: Rich context for music recommendations

## Architecture Principles

### Separation of Concerns
Each interface is independent and focuses on specific use cases:
- **CLI**: Automation, scripting, system administration
- **Web**: Casual browsing, remote access, multi-device support
- **TUI**: Power users, keyboard-driven workflows
- **Graph**: Music discovery, relationship exploration
- **MCP**: AI integration, natural language interaction

### Shared Backend
All interfaces use the same backend components:
- **Database**: Consistent data access across interfaces
- **Player**: Unified MPD integration
- **Configuration**: Same configuration system
- **Sources**: Identical music source management

### Real-time Updates
Interfaces support real-time status monitoring:
- **Player Status**: Current track, playback state, volume
- **Database Changes**: New imports, metadata updates
- **Source Availability**: Real-time source status checking

## Interface Selection Guide

### Use CLI When:
- Automating music management tasks
- Scripting batch operations
- Remote server administration
- Integration with system scripts
- First-time setup and configuration

### Use Web Interface When:
- Casual music browsing and playback
- Multi-device access (tablet, phone, laptop)
- Sharing access with others on network
- Visual playlist management
- Remote music control

### Use TUI When:
- Terminal-based workflows
- Keyboard-driven navigation preferred
- Limited screen real estate
- SSH/remote terminal access
- Power user operations

### Use Graph Explorer When:
- Discovering music relationships
- Visual exploration of collection
- Understanding genre connections
- Finding similar artists or albums
- Music collection analysis

### Use MCP Server When:
- AI-powered music recommendations
- Natural language music queries
- LLM-driven playlist creation
- Conversational music discovery
- Integration with AI assistants

## Configuration

Each interface supports configuration through the main config system:

```yaml
interfaces:
  web:
    host: localhost
    port: 8501
    auto_refresh: true
    refresh_interval: 5
  
  tui:
    theme: dark
    vim_keys: true
    show_help: true
  
  graph:
    host: localhost
    port: 8502
    max_nodes: 200
    layout_algorithm: spring
  
  mcp:
    host: localhost
    port: 8000
    cors_enabled: true
    rate_limit: 100
```

## Usage Examples

```bash
# Launch interfaces
uv run linernodes interface web --port 8501
uv run linernodes interface tui
uv run linernodes interface graph --port 8502
uv run linernodes interface mcp --host 0.0.0.0

# CLI operations
uv run linernodes player play
uv run linernodes database search "jazz"
uv run linernodes sources import-all
```

```python
# Programmatic interface access
from linernodes.interfaces.web import WebInterface
from linernodes.interfaces.tui import TuiInterface

# Start web interface programmatically
web = WebInterface()
web.run()

# Access TUI components
tui = TuiInterface()
tui.run()
```

## Extension Points

The interface system is designed for extensibility:

### Custom Interface Development
```python
from linernodes.backend import DatabaseManager, MpdController

class CustomInterface:
    def __init__(self):
        self.db = DatabaseManager()
        self.player = MpdController()
    
    def run(self):
        # Custom interface implementation
        pass
```

### Plugin Architecture
Future support for interface plugins:
- Mobile app interfaces
- Desktop GUI applications
- Browser extensions
- Smart home integrations
- Voice control interfaces

## Performance Considerations

### Resource Usage
- **CLI**: Minimal resource usage, fast startup
- **Web**: Moderate memory usage, browser-dependent
- **TUI**: Low resource usage, efficient terminal rendering
- **Graph**: Higher memory usage for large collections
- **MCP**: Network overhead, concurrent request handling

### Scalability
- All interfaces support large music collections (10K+ tracks)
- Pagination and lazy loading for performance
- Efficient database queries with proper indexing
- Caching strategies for frequently accessed data
"""

# Interface imports for common usage
from .web import WebInterface
from .graph_explorer import MusicGraphExplorer

# Note: TUI and MCP interfaces are works in progress
# from .tui import TuiInterface  
# from .mcp_server import MCPServer

__all__ = [
    "WebInterface",
    "MusicGraphExplorer", 
]