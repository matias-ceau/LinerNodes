"""
Communicate with MPD via the python-mpd2 module

Provides a controller class for interacting with MPD, with custom configuration
for LinerNodes that follows XDG specifications.
"""

from mpd import MPDClient
import os
import subprocess
import shutil
import pathlib
from xdg import xdg_cache_home, xdg_config_home, xdg_data_home, xdg_state_home

from linernodes.config.config_manager import ConfigManager


class MPDController:
    def __init__(self, socket_path=None, host=None, port=None, use_custom_config=None):
        # Load configuration
        self.config = ConfigManager()
        
        # Use provided values or load from config
        if use_custom_config is None:
            use_custom_config = self.config.get("mpd", "use_custom_config", False)
        if socket_path is None:
            socket_path = self.config.get("mpd", "socket_path", "/run/mpd/socket")
        if host is None:
            host = self.config.get("mpd", "host", "localhost")
        if port is None:
            port = self.config.get("mpd", "port", 6600)
        
        # LinerNodes specific paths
        self.app_name = "linernodes"
        self.app_config_dir = os.path.join(xdg_config_home(), self.app_name)
        self.app_data_dir = os.path.join(xdg_data_home(), self.app_name)
        self.app_state_dir = os.path.join(xdg_state_home(), self.app_name)
        self.app_cache_dir = os.path.join(xdg_cache_home(), self.app_name)
        
        # Custom MPD paths for LinerNodes
        self.mpd_config_file = os.path.join(self.app_config_dir, "mpd.conf")
        self.playlist_dir = os.path.join(self.app_data_dir, "playlists")
        self.db_file = os.path.join(self.app_cache_dir, "mpd.db")
        self.pid_file = os.path.join(self.app_state_dir, "mpd.pid")
        self.state_file = os.path.join(self.app_state_dir, "mpd.state")
        self.log_file = os.path.join(self.app_state_dir, "mpd.log")
        self.custom_socket = os.path.join(self.app_state_dir, "mpd.socket")
        
        # User's music directory from config
        self.music_dir = os.path.expanduser(self.config.get("mpd", "music_dir", "~/music"))

        # Create necessary directories
        for directory in [
            self.app_config_dir, 
            self.app_data_dir, 
            self.app_state_dir, 
            self.app_cache_dir,
            self.playlist_dir
        ]:
            os.makedirs(directory, exist_ok=True)

        # Generate custom config if requested
        if use_custom_config:
            self._generate_mpd_config()
            # Try to start or restart MPD with the custom config if it exists
            self._ensure_mpd_running()
            # Use custom socket
            socket_path = self.custom_socket
            
            # Update config to use custom MPD in the future
            self.config.set("mpd", "use_custom_config", True)

        self.client = MPDClient()

        # Try Unix socket first, fallback to TCP
        try:
            self.client.connect(socket_path)
        except Exception as e:
            try:
                self.client.connect(host, port)
            except Exception as connect_error:
                raise Exception(f"Failed to connect to MPD: {connect_error}. Original error: {e}")

        # Configure MPD settings
        self._configure_mpd()

    def _generate_mpd_config(self):
        """Generate a custom MPD configuration file for LinerNodes with Pipewire support"""
        config = f"""# LinerNodes custom MPD configuration
# Generated automatically - manual changes will be preserved

music_directory     "{self.music_dir}"
playlist_directory  "{self.playlist_dir}"
db_file             "{self.db_file}"
state_file          "{self.state_file}"
pid_file            "{self.pid_file}"
log_file            "{self.log_file}"

# Use a custom socket for LinerNodes
bind_to_address     "{self.custom_socket}"
# Also bind to localhost:6601 for fallback
bind_to_address     "localhost:6601"

# MPD settings
auto_update         "yes"
restore_paused      "yes"
metadata_to_use     "artist,album,title,track,name,genre,date"
follow_outside_symlinks "yes"
follow_inside_symlinks  "yes"

# Audio outputs - Pipewire first as primary
audio_output {{
    type            "pipewire"
    name            "PipeWire Sound Server"
    enabled         "yes"
}}

# ALSA fallback 
audio_output {{
    type            "alsa"
    name            "ALSA Sound Card"
    mixer_type      "software"
    enabled         "no"  # Disabled by default, enable if needed
}}

# Visualizer feed
audio_output {{
    type            "fifo"
    name            "Visualizer feed"
    path            "{self.app_state_dir}/mpd.fifo"
    format          "44100:16:2"
    enabled         "yes"
}}
"""
        # Create config file if it doesn't exist, or update it if needed
        if not os.path.exists(self.mpd_config_file):
            with open(self.mpd_config_file, "w") as f:
                f.write(config)
                
    def _ensure_mpd_running(self):
        """Make sure MPD is running with our custom config"""
        if not os.path.exists(self.mpd_config_file):
            return
            
        # Check if MPD is already running with our config
        if os.path.exists(self.pid_file):
            try:
                with open(self.pid_file, "r") as f:
                    pid = int(f.read().strip())
                # Check if process is running
                os.kill(pid, 0)
                # Process exists, so MPD is running
                return
            except (ProcessLookupError, ValueError, FileNotFoundError, PermissionError):
                # PID file exists but process is not running or invalid
                pass
                
        # Try to start MPD with our custom config
        try:
            # Check if mpd is available
            if shutil.which("mpd") is not None:
                subprocess.run(
                    ["mpd", self.mpd_config_file], 
                    check=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
        except subprocess.SubprocessError:
            # Could not start MPD, will fall back to system instance
            pass
            
    def _configure_mpd(self):
        """Set MPD configuration from config file"""
        # Get audio settings from config
        defaults = {
            "consume": 1 if self.config.get("audio", "consume", False) else 0,
            "random": 1 if self.config.get("audio", "random", False) else 0,
            "repeat": 1 if self.config.get("audio", "repeat", False) else 0,
            "volume": self.config.get("audio", "volume", 70),
            "crossfade": self.config.get("audio", "crossfade", 2),
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
