from pathlib import Path
from typing import Dict, Any
from linernodes.config.config_manager import ConfigManager


class MPDConfig:
    def __init__(self, config_manager: ConfigManager) -> None:
        self.config_manager = config_manager
        # Use the TOML structure which has mpd section
        self.mpd_config: Dict[str, Any] = self.config_manager.get_all().get("mpd", {})

    def get_mpd_path(self) -> Path:
        """Get the MPD data path."""
        # Get data path from the mpd section with socket_path as fallback
        path_str = self.mpd_config.get("socket_path")
        if path_str:
            return Path(path_str)
        # Default to the first config path found
        config_paths = self.config_manager._get_config_paths()
        if config_paths:
            return config_paths[0].parent / "mpd"
        # Fallback to a default path if no config files are found
        return Path.home() / ".config" / "linernodes" / "mpd"

    def get_host(self) -> str:
        """Get MPD host."""
        return self.mpd_config.get("host", "localhost")

    def get_port(self) -> int:
        """Get MPD port."""
        return int(self.mpd_config.get("port", 6600))
