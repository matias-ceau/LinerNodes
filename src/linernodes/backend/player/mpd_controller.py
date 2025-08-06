import os
import subprocess
import shutil
from pathlib import Path
from mpd import MPDClient
from xdg import xdg_config_home, xdg_data_home, xdg_state_home, xdg_cache_home

from linernodes.config.config_manager import ConfigManager

# Lightweight logging (no hard dependency on setup)
try:
    from linernodes.logging.setup import get_logger

    _logger = get_logger("linernodes.mpd")
except Exception:  # pragma: no cover
    import logging as _fallback_logging

    _logger = _fallback_logging.getLogger("linernodes.mpd")


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

        # Autospawn policy (Phase 0): keep enabled by default
        # Priority: ENV override > config value > default True
        env_autospawn = os.getenv("LINERNODES_MPD_AUTOSPAWN")
        if env_autospawn is not None:
            self.autospawn_enabled = env_autospawn in ("1", "true", "TRUE", "yes", "on")
        else:
            self.autospawn_enabled = bool(mpd_cfg.get("autospawn", True))
        _logger.debug(
            "MPD autospawn policy evaluated",
            extra={"operation": "mpd_policy", "autospawn": self.autospawn_enabled},
        )

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

        # If custom config is enabled, generate config; spawn based on policy
        if self.use_custom_config:
            self._generate_mpd_config()
            if self.autospawn_enabled:
                _logger.info(
                    "Ensuring MPD is running (autospawn enabled)",
                    extra={"operation": "mpd_spawn"},
                )
                self._ensure_mpd_running()
            else:
                _logger.info(
                    "Skipping MPD autospawn per policy",
                    extra={"operation": "mpd_spawn"},
                )
            self.socket_path = str(self.custom_socket)
            self.config.set("mpd", "use_custom_config", True)  # persist flag if needed

        self.client = MPDClient()
        # Try connection via socket first, fallback to TCP
        try:
            self.client.connect(self.socket_path)
            _logger.debug(
                "Connected to MPD via socket",
                extra={"operation": "mpd_connect", "endpoint": self.socket_path},
            )
        except Exception as e:
            _logger.warning(
                "Socket connect failed, trying TCP",
                extra={"operation": "mpd_connect", "error": str(e)},
            )
            try:
                self.client.connect(self.host, self.port)
                _logger.debug(
                    "Connected to MPD via TCP",
                    extra={
                        "operation": "mpd_connect",
                        "endpoint": f"{self.host}:{self.port}",
                    },
                )
            except Exception as connect_error:
                _logger.error(
                    "Failed to connect to MPD",
                    extra={
                        "operation": "mpd_connect",
                        "socket_error": str(e),
                        "tcp_error": str(connect_error),
                    },
                )
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
            _logger.warning(
                "MPD config file missing; cannot start MPD",
                extra={"operation": "mpd_spawn"},
            )
            return

        # Check if MPD is already running with our config (by PID file)
        if self.pid_file.exists():
            try:
                with self.pid_file.open("r") as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)
                _logger.debug(
                    "MPD already running (pid file present)",
                    extra={"operation": "mpd_spawn", "pid": pid},
                )
                return  # process exists
            except Exception:
                _logger.info(
                    "Stale PID file detected; attempting restart",
                    extra={"operation": "mpd_spawn"},
                )

        # Start MPD via system command if available
        if shutil.which("mpd") is not None:
            try:
                result = subprocess.run(
                    ["mpd", str(self.mpd_config_file)],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                _logger.info(
                    "MPD started",
                    extra={"operation": "mpd_spawn", "returncode": result.returncode},
                )
            except subprocess.SubprocessError as e:
                _logger.error(
                    "Failed to start MPD",
                    extra={"operation": "mpd_spawn", "error": str(e)},
                )
        else:
            _logger.error(
                "MPD binary not found in PATH", extra={"operation": "mpd_spawn"}
            )

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

    def update_database(self):
        """Update MPD database."""
        self.client.update()

    def get_status(self):
        """Get MPD status."""
        return self.client.status()

    def get_playlist(self):
        """Get current playlist."""
        return self.client.playlistinfo()

    def play(self, pos=None):
        """Play music (optionally at specific position)."""
        if pos is not None:
            self.client.play(pos)
        else:
            self.client.play()

    def pause(self):
        self.client.pause()

    def stop(self):
        """Stop playback."""
        self.client.stop()

    def next(self):
        """Skip to next track."""
        self.client.next()

    def previous(self):
        """Skip to previous track."""
        self.client.previous()

    def set_volume(self, volume: int):
        """Set volume (0-100)."""
        self.client.setvol(max(0, min(100, volume)))

    def add_to_playlist(self, file_path: str):
        self.client.add(file_path)

    def clear_playlist(self):
        self.client.clear()

    def get_current_song(self):
        return self.client.currentsong()

    def list_all_files(self):
        """List all files in music directory."""
        return self.client.listall()

    def search_files(self, pattern: str = ""):
        """Search for files matching pattern."""
        files = self.client.listall()
        matching_files = []
        for item in files:
            if "file" in item and pattern.lower() in item["file"].lower():
                matching_files.append(item["file"])
        return matching_files[:10]  # Return first 10 matches

    def get_albums(self):
        """Get all albums (directories) in the music library."""
        albums = set()
        files = self.client.listall()
        for item in files:
            if "file" in item:
                # Extract album directory (first two path components typically)
                path_parts = item["file"].split("/")
                if len(path_parts) >= 2:
                    album_path = "/".join(path_parts[:2])
                    albums.add(album_path)
        return sorted(list(albums))

    def add_album_to_playlist(self, album_path: str):
        """Add all files from an album directory to playlist."""
        files = self.client.listall()
        added_files = []
        for item in files:
            if "file" in item and item["file"].startswith(album_path + "/"):
                self.client.add(item["file"])
                added_files.append(item["file"])
        return added_files

    def load_random_albums(self, count: int = 10):
        """Load random albums into the playlist."""
        import random

        albums = self.get_albums()
        if albums:
            selected = random.sample(albums, min(count, len(albums)))
            for album in selected:
                self.add_album_to_playlist(album)
            return selected
        return []

    def __del__(self):
        try:
            self.client.close()
            self.client.disconnect()
        except Exception:
            pass
