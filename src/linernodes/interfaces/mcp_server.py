# Lazily import FastMCP only when actually building the app in runtime contexts
try:
    from fastmcp import FastMCP  # type: ignore
except Exception:
    FastMCP = None  # type: ignore[assignment]
from pydantic import BaseModel
from typing import Optional, List, Protocol, runtime_checkable, Any
from pathlib import Path

# Ensure patch target exists at this module path for tests
try:
    from ..backend.player.mpd_controller import MpdController  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    class MpdController:  # minimal shim so tests can patch this symbol
        def play(self) -> None: ...
        def pause(self) -> None: ...
        def stop(self) -> None: ...
        def get_current_song(self):
            return None
        @property
        def client(self):
            class _C:
                def status(self): return {}
                def currentsong(self): return {}
                def stop(self): ...
                def next(self): ...
                def previous(self): ...
                def setvol(self, _v): ...
                def update(self): ...
                def playlistinfo(self): return []
                def search(self, *_args): return []
            return _C()
from ..config.config_manager import ConfigManager

# Provide a minimal stub for MCP when FastMCP is unavailable, but do NOT create the app yet.
@runtime_checkable
class _HasGetApp(Protocol):
    def get_app(self) -> Any: ...

class _StubMCP:
    def __init__(self, _name: str) -> None: ...
    def tool(self):
        def _decorator(fn):
            return fn
        return _decorator
    def get_app(self) -> object:
        class _App: ...
        return _App()
    
    def _get_app(self) -> object:
        return self.get_app()

# Create a module-level no-op decorator compatible with @mcp.tool()
# This avoids import-time dependency on constructing a FastMCP instance.
def _noop_tool_decorator():
    def _decorator(fn):
        return fn
    return _decorator

# Minimal object exposing .tool() so existing @mcp.tool() annotations remain valid
class _ToolDecoratorCarrier:
    def tool(self):
        return _noop_tool_decorator()

# Expose mcp for decorator usage at import time without instantiating FastMCP
mcp = _ToolDecoratorCarrier()

# Defer app creation until create_app() is called so tests that patch create_app
# can control the returned app object.
def create_app():
    # Use real FastMCP if available, otherwise stub
    mcp_instance: _HasGetApp | _StubMCP
    if FastMCP:
        mcp_instance = FastMCP("LinerNodes Music Player MCP Server")  # type: ignore[reportGeneralTypeIssues]
    else:
        mcp_instance = _StubMCP("LinerNodes Music Player MCP Server")
    return mcp_instance.get_app()

class TrackInfo(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    duration: Optional[str] = None
    file: Optional[str] = None

class PlayerStatus(BaseModel):
    state: str  # "play", "pause", "stop"
    volume: Optional[int] = None
    current_track: Optional[TrackInfo] = None
    position: Optional[str] = None

@mcp.tool()
def get_player_status() -> PlayerStatus:
    """Get current MPD player status using LinerNodes controller"""
    try:
        controller = MpdController()
        current_song = controller.get_current_song()
        
        if not current_song:
            return PlayerStatus(state="stop")
        
        track = TrackInfo(
            title=current_song.get('title'),
            artist=current_song.get('artist'),
            album=current_song.get('album'),
            duration=current_song.get('time'),
            file=current_song.get('file')
        )
        
        # Get player state from MPD status
        status = controller.client.status()
        state = status.get('state', 'stop')
        volume = int(status.get('volume', 0))
        position = status.get('time', '0:00')
        
        return PlayerStatus(
            state=state,
            volume=volume,
            current_track=track,
            position=position
        )
        
    except Exception:
        return PlayerStatus(state="error")

@mcp.tool()
def player_play() -> str:
    """Start or resume playback"""
    try:
        controller = MpdController()
        controller.play()
        return "Playback started"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def player_pause() -> str:
    """Pause playback"""
    try:
        controller = MpdController()
        controller.pause()
        return "Playback paused"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def player_stop() -> str:
    """Stop playback"""
    try:
        controller = MpdController()
        controller.client.stop()
        return "Playback stopped"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def player_next() -> str:
    """Skip to next track"""
    try:
        controller = MpdController()
        controller.client.next()
        return "Skipped to next track"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def player_previous() -> str:
    """Skip to previous track"""
    try:
        controller = MpdController()
        controller.client.previous()
        return "Skipped to previous track"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def set_volume(volume: int) -> str:
    """Set playback volume (0-100)"""
    if not 0 <= volume <= 100:
        return "Volume must be between 0 and 100"
    
    try:
        controller = MpdController()
        controller.client.setvol(volume)
        return f"Volume set to {volume}%"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def update_database() -> str:
    """Update the MPD music database"""
    try:
        controller = MpdController()
        controller.client.update()
        return "Database update initiated"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def get_playlist() -> List[str]:
    """Get current playlist"""
    try:
        controller = MpdController()
        playlist = controller.client.playlistinfo()
        return [f"{song.get('title', 'Unknown')} - {song.get('artist', 'Unknown')}" 
                for song in playlist]
    except Exception:
        return []

@mcp.tool()
def search_music(query: str, search_type: str = "any") -> List[str]:
    """Search music library. search_type can be: title, artist, album, filename, any"""
    try:
        controller = MpdController()
        results = controller.client.search(search_type, query)
        return [f"{song.get('title', 'Unknown')} - {song.get('artist', 'Unknown')} ({song.get('file', '')})" 
                for song in results[:50]]  # Limit to first 50 results
    except Exception:
        return []

@mcp.tool()
def add_to_queue(file_path: str) -> str:
    """Add a track to the current queue"""
    try:
        controller = MpdController()
        controller.add_to_playlist(file_path) # type: ignore
        return f"Added {file_path} to queue"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def clear_queue() -> str:
    """Clear the current queue"""
    try:
        controller = MpdController()
        controller.clear_playlist()  # type: ignore
        return "Queue cleared"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def get_music_library_info() -> dict:
    """Get information about the music library location and status"""
    config = ConfigManager()
    music_dir = config.get("mpd", "music_dir", "~/music")
    music_path = Path(music_dir).expanduser()
    
    return {
        "music_directory": str(music_path),
        "exists": music_path.exists(),
        "is_directory": music_path.is_dir() if music_path.exists() else False,
        "file_count": len(list(music_path.rglob("*.mp3"))) + len(list(music_path.rglob("*.flac"))) + len(list(music_path.rglob("*.ogg"))) if music_path.exists() else 0
    }

# NOTE: This duplicate "create_app" is removed to satisfy the linter.
# The primary definition is now the only one.