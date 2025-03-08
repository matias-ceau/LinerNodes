"""
Configuration manager for LinerNodes

This module handles reading and writing TOML configuration files
for LinerNodes application settings.
"""

import os
import tomli
import tomli_w
from xdg import xdg_config_home

DEFAULT_CONFIG = {
    "mpd": {
        "use_custom_config": True,
        "music_dir": "~/music",
        "host": "localhost",
        "port": 6600,
        "socket_path": "/run/mpd/socket",
    },
    "audio": {
        "volume": 70,
        "crossfade": 2,
        "consume": False,
        "random": False,
        "repeat": False,
    },
    "interface": {"theme": "default", "show_album_art": True},
}


class ConfigManager:
    """Manages LinerNodes configuration settings"""

    def __init__(self):
        self.app_name = "linernodes"
        self.config_dir = os.path.join(xdg_config_home(), self.app_name)
        self.config_file = os.path.join(self.config_dir, "config.toml")

        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)

        # Load or create default config
        self.config = self._load_config()

    def _load_config(self):
        """Load configuration from file or create default if not exists"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "rb") as f:
                    return tomli.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return DEFAULT_CONFIG.copy()
        else:
            # Create default config file
            self._save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()

    def _save_config(self, config=None):
        """Save configuration to file"""
        if config is None:
            config = self.config

        try:
            with open(self.config_file, "wb") as f:
                tomli_w.dump(config, f)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, section, key, default=None):
        """Get a configuration value"""
        try:
            return self.config.get(section, {}).get(key, default)
        except Exception:
            return default

    def set(self, section, key, value):
        """Set a configuration value"""
        if section not in self.config:
            self.config[section] = {}

        self.config[section][key] = value
        self._save_config()

    def get_all(self):
        """Get the entire configuration"""
        return self.config.copy()

    def update(self, new_config):
        """Update multiple configuration values at once"""
        # Deep update the config
        for section, values in new_config.items():
            if section not in self.config:
                self.config[section] = {}

            if isinstance(values, dict):
                for key, value in values.items():
                    self.config[section][key] = value

        self._save_config()
