"""Player - MPD Integration and Playback Control.

This module provides comprehensive integration with MPD (Music Player Daemon)
for music playback control, playlist management, and real-time status monitoring.

## Architecture

### MPD Integration
- **Connection Management**: Robust connection handling with reconnection logic
- **XDG Compliance**: Follows XDG Base Directory specification for configuration
- **Auto Configuration**: Intelligent MPD setup with sensible defaults
- **Error Recovery**: Graceful handling of connection failures and timeouts

### Features

#### Playback Control
- Play, pause, stop, next, previous commands
- Volume control with validation
- Seek functionality for track navigation
- Crossfade and audio settings management

#### Playlist Management
- Add tracks, albums, or entire directories
- Clear, shuffle, and repeat modes
- Dynamic playlist modification
- Queue management and track ordering

#### Real-time Monitoring
- Current track information with metadata
- Playback status (playing, paused, stopped)
- Progress tracking with time elapsed/remaining
- Volume and audio device monitoring

#### Library Integration
- Music database scanning and updates
- File path resolution and validation
- Metadata synchronization with internal database
- Source availability checking

## Configuration Management

### XDG Directory Structure
```
~/.config/linernodes/       # Configuration files
~/.local/share/linernodes/   # Database and user data  
~/.local/state/linernodes/   # MPD state and logs
~/.cache/linernodes/         # Temporary files and cache
```

### MPD Configuration
Automatic generation of MPD configuration with:
- Music directory detection
- Audio output configuration
- Database and state file locations
- Network and security settings

## Usage Examples

```python
from linernodes.backend.player import MpdController

# Initialize controller
controller = MpdController()

# Playback control
controller.play()
controller.pause()
controller.next_track()
controller.set_volume(75)

# Status monitoring
status = controller.get_status()
current_song = controller.get_current_song()
queue = controller.get_playlist()

# Playlist management
controller.add_to_playlist("/path/to/song.mp3")
controller.clear_playlist()
controller.shuffle_playlist()
```

## Error Handling

Robust error handling for common scenarios:
- MPD daemon not running
- Network connectivity issues
- Invalid file paths or missing files
- Permission and access problems
- Configuration file corruption

## Integration Points

### Database Synchronization
The player module integrates with the database system to:
- Resolve track IDs to file paths
- Update play counts and statistics
- Sync availability status
- Cache frequently accessed metadata

### Interface Communication
Provides consistent API for all interfaces:
- Real-time status updates
- Event notification system
- Asynchronous operation support
- Thread-safe operations
"""

from .mpd_controller import MpdController
from .mpd_config import MpdConfig

__all__ = [
    "MpdController",
    "MpdConfig",
]