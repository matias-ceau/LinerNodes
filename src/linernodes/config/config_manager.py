import os
from pathlib import Path
from typing import Dict, Any
import yaml


class ConfigManager:
    def __init__(self) -> None:
        self.config: Dict[str, Any] = {}
        self.config_file = self._get_config_path()
        self.load_config()

    def _get_config_path(self) -> Path:
        # Use XDG_CONFIG_HOME if available, else default to ~/.config
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            base_path = Path(xdg_config)
        else:
            base_path = Path.home() / ".config"

        return base_path / "linernodes" / "config.yaml"

    def load_config(self) -> None:
        if not self.config_file.exists():
            self._create_default_config()

        with self.config_file.open("r") as f:
            self.config = yaml.safe_load(f)

    def _create_default_config(self) -> None:
        # Create parent directories if they don't exist
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        default_config = {
            "mpd": {
                "path": str(self.config_file.parent / "mpd"),
                "host": "localhost",
                "port": 6600,
            }
        }

        with self.config_file.open("w") as f:
            yaml.dump(default_config, f)

        self.config = default_config

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self.config.get(key, default)
