# Music Context Player

A comprehensive music player system with CLI, TUI, and web interfaces integrated with MPD (Music Player Daemon) and FastMCP.

## Project Structure

- **CLI**: Click-based command line interface with MPD setup automation
- **TUI**: Textual-based terminal user interface for interactive control
- **Web**: Streamlit-based web interface for browser access
- **Server**: FastMCP server for external integrations

## Music Library

- Music library location: `/mnt/hdd4t/MEGA/UnifiedLibrary/music/`

## Commands

### MPD Management
- `music-context-player mpd setup` - Configure and start MPD service

### Interface Launchers
- `music-context-player tui` - Launch terminal interface
- `music-context-player web` - Launch web interface
- `music-context-player server` - Start MCP server

## Development

- Built with `uv` package manager
- Dependencies: Click, FastMCP, Rich, Textual, Streamlit
- Uses systemd user services for MPD management

## Important Instruction Reminders

Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.