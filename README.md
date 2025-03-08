# Music Controller

This is a simple music controller application that interfaces with MPD (Music Player Daemon) and manages a local music database using DuckDB.

## Features

- Play and pause music through MPD
- Add songs to the MPD playlist
- View currently playing song
- Store and retrieve song metadata using DuckDB

## Module Functions

### backend/mpd_client.py
- `MPDController`: Handles communication with MPD server
  - `play()`: Start playing music
  - `pause()`: Pause music playback
  - `add_to_playlist(file_path)`: Add a song to the MPD playlist
  - `get_current_song()`: Get information about the currently playing song

### cli/commands.py
- Implements Click commands for CLI interaction
  - `play`: Start playing music
  - `pause`: Pause music playback
  - `add`: Add a song to the playlist
  - `current`: Show information about the currently playing song

### database/db_manager.py
- `DatabaseManager`: Manages interaction with DuckDB
  - `create_tables()`: Create necessary database tables
  - `add_song(title, artist, album, file_path)`: Add a song to the database
  - `get_songs()`: Retrieve all songs from the database

## Setup and Usage

1. Install required dependencies:
   ```
   pip install .
   ```

2. Run the application:
   ```
   # Generate a custom MPD configuration file
   linernodes generate-config
   
   # Restart the custom MPD instance
   linernodes restart-mpd
   ```

   Available commands: play, pause, add, current, generate-config, restart-mpd, config

### Configuration System

LinerNodes uses a TOML configuration file stored at `$XDG_CONFIG_HOME/linernodes/config.toml`. You can manage this configuration through the CLI:

```
# View all configuration settings
linernodes config get

# View settings in a specific section
linernodes config get mpd

# View a specific setting
linernodes config get mpd music_dir

# Change a setting
linernodes config set mpd music_dir "~/Music"

# Set default MPD mode (custom or system)
linernodes config set-default --custom-mpd
```

Default configuration includes:

```toml
[mpd]
use_custom_config = false
music_dir = "~/music"
host = "localhost"
port = 6600
socket_path = "/run/mpd/socket"

[audio]
volume = 70
crossfade = 2
consume = false
random = false
repeat = false

[interface]
theme = "default"
show_album_art = true
```

### Custom MPD Configuration

LinerNodes can create and manage its own MPD configuration with the following features:

- MPD configuration stored in `$XDG_CONFIG_HOME/linernodes/mpd.conf`
- LinerNodes configuration stored in `$XDG_CONFIG_HOME/linernodes/config.toml`
- Data files stored in appropriate XDG directories:
  - Playlists: `$XDG_DATA_HOME/linernodes/playlists`
  - Database: `$XDG_CACHE_HOME/linernodes/mpd.db`
  - State and logs: `$XDG_STATE_HOME/linernodes/`
- Uses your music directory specified in config (defaults to `~/music`)
- Configured with Pipewire support out of the box
- Runs on custom socket to avoid conflicts with system MPD

## Future Improvements

- Implement playlist management
- Add more advanced querying capabilities
- Integrate with external metadata sources
