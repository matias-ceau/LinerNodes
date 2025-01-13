"""
Communicate with MPD via the python-mpd2 module

Inputs :
    - path (either 

Outputs : 
    - MPD action
    - write to state files ?
"""

from mpd import MPDClient


from mpd import MPDClient
import os
from xdg import xdg_cache_home, xdg_config_home, xdg_data_home


class MPDController:
    def __init__(self, socket_path="/run/mpd/socket", host="localhost", port=6600):

        # XDG compliant paths
        self.config_dir = os.path.join(xdg_config_home(), "mpd")
        self.music_dir = os.path.join(xdg_data_home(), "music")
        self.playlist_dir = os.path.join(self.config_dir, "playlists")
        self.db_file = os.path.join(xdg_cache_home(), "mpd/database")

        # Create directories if they don't exist
        for directory in [self.config_dir, self.music_dir, self.playlist_dir]:
            os.makedirs(directory, exist_ok=True)

        self.client = MPDClient()

        # Try Unix socket first, fallback to TCP
        try:
            self.client.connect(socket_path)
        except:
            self.client.connect(host, port)

        # Configure MPD settings
        self._configure_mpd()

    def _configure_mpd(self):
        """Set default MPD configuration"""
        defaults = {
            "consume": 0,
            "random": 0,
            "repeat": 0,
            "volume": 70,
            "crossfade": 2,
        }

        for setting, value in defaults.items():
            try:
                getattr(self.client, setting)(value)
            except:
                pass

    def __del__(self):
        """Clean disconnect"""
        try:
            self.client.close()
            self.client.disconnect()
        except:
            pass

    # Your existing methods remain the same
    def play(self):
        self.client.play()

    def pause(self):
        self.client.pause()

    def add_to_playlist(self, file_path):
        self.client.add(file_path)

    def clear_playlist(self):
        self.client.clear()

    def get_current_song(self):
        return self.client.currentsong()
