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
   pip install click python-mpd2 duckdb
   ```

2. Ensure MPD is running on your system

3. Run the application:
   ```
   python main.py [COMMAND]
   ```

   Available commands: play, pause, add, current

## Future Improvements

- Implement playlist management
- Add more advanced querying capabilities
- Integrate with external metadata sources
