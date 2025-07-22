from fastmcp import FastMCP
from pydantic import BaseModel
from typing import Optional, List
import subprocess
import json
from pathlib import Path

# Initialize FastMCP server
mcp = FastMCP("Music Context Player MCP Server")

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
def get_mpd_status() -> PlayerStatus:
    """Get current MPD player status"""
    try:
        result = subprocess.run(["mpc", "status", "-f", "%title%|%artist%|%album%|%time%|%file%"], 
                              capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        if len(lines) < 2:
            return PlayerStatus(state="stop")
        
        # Parse track info
        track_parts = lines[0].split('|') if lines[0] else ["", "", "", "", ""]
        track = TrackInfo(
            title=track_parts[0] or None,
            artist=track_parts[1] or None,
            album=track_parts[2] or None,
            duration=track_parts[3] or None,
            file=track_parts[4] or None
        )
        
        # Parse status line
        status_line = lines[1] if len(lines) > 1 else ""
        state = "stop"
        volume = None
        position = None
        
        if "[playing]" in status_line:
            state = "play"
        elif "[paused]" in status_line:
            state = "pause"
        
        # Extract volume and position from status line
        # Format: [playing] #1/234   0:15/3:42 (7%)   volume: 85%
        if "volume:" in status_line:
            volume_part = status_line.split("volume:")[-1].strip()
            volume = int(volume_part.replace('%', '').strip())
        
        return PlayerStatus(state=state, volume=volume, current_track=track, position=position)
        
    except subprocess.CalledProcessError:
        return PlayerStatus(state="error")

@mcp.tool()
def mpd_play() -> str:
    """Start or resume playback"""
    try:
        subprocess.run(["mpc", "play"], check=True)
        return "Playback started"
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"

@mcp.tool()
def mpd_pause() -> str:
    """Pause playback"""
    try:
        subprocess.run(["mpc", "pause"], check=True)
        return "Playback paused"
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"

@mcp.tool()
def mpd_stop() -> str:
    """Stop playback"""
    try:
        subprocess.run(["mpc", "stop"], check=True)
        return "Playback stopped"
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"

@mcp.tool()
def mpd_next() -> str:
    """Skip to next track"""
    try:
        subprocess.run(["mpc", "next"], check=True)
        return "Skipped to next track"
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"

@mcp.tool()
def mpd_prev() -> str:
    """Skip to previous track"""
    try:
        subprocess.run(["mpc", "prev"], check=True)
        return "Skipped to previous track"
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"

@mcp.tool()
def set_volume(volume: int) -> str:
    """Set playback volume (0-100)"""
    if not 0 <= volume <= 100:
        return "Volume must be between 0 and 100"
    
    try:
        subprocess.run(["mpc", "volume", str(volume)], check=True)
        return f"Volume set to {volume}%"
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"

@mcp.tool()
def update_database() -> str:
    """Update the MPD music database"""
    try:
        subprocess.run(["mpc", "update"], check=True)
        return "Database update initiated"
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"

@mcp.tool()
def get_playlist() -> List[str]:
    """Get current playlist"""
    try:
        result = subprocess.run(["mpc", "playlist", "-f", "%title% - %artist%"], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        return []

@mcp.tool()
def search_music(query: str, search_type: str = "any") -> List[str]:
    """Search music library. search_type can be: title, artist, album, filename, any"""
    try:
        result = subprocess.run(["mpc", "search", search_type, query], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        return []

# Create the FastAPI app
app = mcp.get_app()