import os
import subprocess
import shutil
from pathlib import Path
from mpd import MPDClient
from xdg import xdg_config_home, xdg_data_home, xdg_state_home, xdg_cache_home

from linernodes.config.config_manager import ConfigManager


class MpdController:
    def __init__(self) -> None:
        # Load general config from config.toml via ConfigManager
        self.config = ConfigManager()
        mpd_cfg = self.config.get_all().get("mpd", {})

        # Read MPD parameters from config
        self.use_custom_config = True
        self.socket_path = mpd_cfg.get("socket_path", "/run/mpd/socket")
        self.host = mpd_cfg.get("host", "localhost")
        self.port = int(mpd_cfg.get("port", 6600))
        self.music_dir = os.path.expanduser(mpd_cfg.get("music_dir", "~/music"))

        # XDG-based application directories
        self.app_name = "linernodes"
        self.app_config_dir = Path(xdg_config_home()) / self.app_name
        self.app_data_dir = Path(xdg_data_home()) / self.app_name
        self.app_state_dir = Path(xdg_state_home()) / self.app_name
        self.app_cache_dir = Path(xdg_cache_home()) / self.app_name

        # Custom MPD paths using pathlib
        self.mpd_config_file = self.app_config_dir / "mpd.conf"
        self.playlist_dir = self.app_data_dir / "playlists"
        self.db_file = self.app_cache_dir / "mpd.db"
        self.pid_file = self.app_state_dir / "mpd.pid"
        self.state_file = self.app_state_dir / "mpd.state"
        self.log_file = self.app_state_dir / "mpd.log"
        self.custom_socket = self.app_state_dir / "mpd.socket"

        # Create necessary directories using Path.mkdir
        for directory in [
            self.app_config_dir,
            self.app_data_dir,
            self.app_state_dir,
            self.app_cache_dir,
            self.playlist_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

        # If custom config is enabled, generate and ensure MPD is running with it
        if self.use_custom_config:
            self._generate_mpd_config()
            self._ensure_mpd_running()
            self.socket_path = str(self.custom_socket)
            self.config.set("mpd", "use_custom_config", True)  # persist flag if needed

        self.client = MPDClient()
        # Try connection via socket first, fallback to TCP
        try:
            self.client.connect(self.socket_path)
        except Exception as e:
            try:
                self.client.connect(self.host, self.port)
            except Exception as connect_error:
                raise Exception(
                    f"Failed to connect to MPD: {connect_error}. Original error: {e}"
                )

        self._configure_mpd()

    def _generate_mpd_config(self):
        """Generate a custom MPD configuration file with Pipewire support."""
        config_text = f"""# LinerNodes custom MPD configuration
# Generated automatically - manual changes will be preserved

music_directory     "{self.music_dir}"
playlist_directory  "{self.playlist_dir}"
db_file             "{self.db_file}"
state_file          "{self.state_file}"
pid_file            "{self.pid_file}"
log_file            "{self.log_file}"

# Use a custom socket for LinerNodes
bind_to_address     "{self.custom_socket}"
# Also bind to fallback TCP port localhost:6601
bind_to_address     "localhost:6601"

# MPD settings
auto_update         "yes"
restore_paused      "yes"
metadata_to_use     "artist,album,title,track,name,genre,date"
follow_outside_symlinks "yes"
follow_inside_symlinks  "yes"

# Audio outputs - Pipewire primary
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
    enabled         "no"
}}

# Visualizer feed
audio_output {{
    type            "fifo"
    name            "Visualizer feed"
    path            "{self.app_state_dir / "mpd.fifo"}"
    format          "44100:16:2"
    enabled         "yes"
}}
"""
        if not self.mpd_config_file.exists():
            self.mpd_config_file.write_text(config_text)

    def _ensure_mpd_running(self):
        """Ensure MPD is running with our custom configuration."""
        if not self.mpd_config_file.exists():
            return

        # Check if MPD is already running with our config (by PID file)
        if self.pid_file.exists():
            try:
                with self.pid_file.open("r") as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)
                return  # process exists
            except Exception:
                pass

        # Start MPD via system command if available
        if shutil.which("mpd") is not None:
            try:
                subprocess.run(
                    ["mpd", str(self.mpd_config_file)],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            except subprocess.SubprocessError:
                pass

    def _configure_mpd(self):
        """Configure MPD settings based on config."""
        # Audio settings defaults from config
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
            except Exception:
                pass

    def play(self):
        self.client.play()

    def pause(self):
        self.client.pause()

    def add_to_playlist(self, file_path: str):
        self.client.add(file_path)

    def clear_playlist(self):
        self.client.clear()

    def get_current_song(self):
        return self.client.currentsong()

    def __del__(self):
        try:
            self.client.close()
            self.client.disconnect()
        except Exception:
            pass
