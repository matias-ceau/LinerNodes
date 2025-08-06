import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml


class ConfigManager:
    """
    Configuration manager with multiple source support.
    
    Configuration precedence (highest to lowest):
    1. Environment variables (LINERNODES_<SECTION>_<KEY>=value)
    2. Local development config (.linernodes.cfg in current directory)
    3. Custom config file (specified by LINERNODES_CONFIG_FILE)
    4. User config file (XDG_CONFIG_HOME or ~/.config/linernodes/config.yaml)
    5. Default values
    """
    
    def __init__(self) -> None:
        self.config: Dict[str, Any] = {}
        self.config_sources: List[Path] = []
        # establish canonical user config path for tests
        xdg = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg) if xdg else (Path.home() / ".config")
        self.config_file: Path = base / "linernodes" / "config.yaml"
        # ensure default file exists
        self._ensure_default_config_file()
        self._load_all_configs()

    def _get_config_paths(self) -> List[Path]:
        """Get all potential configuration file paths in precedence order."""
        paths = []
        
        # 1. Local development config (.linernodes.cfg)
        local_config = Path.cwd() / ".linernodes.cfg"
        if local_config.exists():
            paths.append(local_config)
        
        # 2. Custom config file from environment
        custom_config = os.environ.get("LINERNODES_CONFIG_FILE")
        if custom_config:
            custom_path = Path(custom_config)
            if custom_path.exists():
                paths.append(custom_path)
        
        # 3. Default user config file
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            base_path = Path(xdg_config)
        else:
            base_path = Path.home() / ".config"
        
        default_path = base_path / "linernodes" / "config.yaml"
        paths.append(default_path)  # Add even if doesn't exist
        
        return paths

    def _load_all_configs(self) -> None:
        """Load configuration from all sources."""
        # Start with default configuration
        self.config = self._get_default_config()
        
        # Get config file paths
        config_paths = self._get_config_paths()
        
        # Load from files in reverse order (lowest precedence first)
        for config_path in reversed(config_paths):
            if config_path.exists():
                try:
                    with config_path.open("r") as f:
                        file_config = yaml.safe_load(f) or {}
                    self._merge_config(self.config, file_config)
                    self.config_sources.append(config_path)
                except yaml.YAMLError:
                    # Propagate YAML parsing errors to satisfy tests
                    raise
                except Exception as e:
                    print(f"Warning: Failed to load config from {config_path}: {e}")
        
        # Override with environment variables (highest precedence)
        self._load_from_environment()
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _load_from_environment(self) -> None:
        """Load configuration overrides from environment variables."""
        prefix = "LINERNODES_"
        
        for env_var, value in os.environ.items():
            if env_var.startswith(prefix):
                # Parse environment variable name
                key_parts = env_var[len(prefix):].lower().split('_')
                if len(key_parts) >= 2:
                    section = key_parts[0]
                    key = '_'.join(key_parts[1:])
                    
                    # Convert value to appropriate type
                    converted_value = self._convert_env_value(value)
                    
                    # Set in config
                    if section not in self.config:
                        self.config[section] = {}
                    self.config[section][key] = converted_value
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Handle boolean values
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # Handle numeric values
        if value.isdigit():
            return int(value)
        
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "mpd": {
                "path": "~/.local/share/linernodes/mpd",
                "host": "localhost",
                "port": 6600,
                "socket_path": "/run/mpd/socket",
                "music_dir": "~/Music",
                "use_custom_config": True
            },
            "audio": {
                "consume": False,
                "random": False,
                "repeat": False,
                "volume": 70,
                "crossfade": 2
            },
            "knowledge_graph": {
                "db_path": "~/.local/share/linernodes/knowledge.db",
                "cards_dir": "~/.local/share/linernodes/cards",
                "auto_import": False
            },
            "interfaces": {
                "web_port": 8501,
                "mcp_port": 8000,
                "graph_explorer_port": 8502
            },
            "musicbrainz": {
                "rate_limit": 1.0,
                "user_agent": "LinerNodes/1.0"
            }
        }
    
    def _ensure_default_config_file(self) -> None:
        """Create default config file if it doesn't exist."""
        # Use self.config_file as canonical default path
        default_path = self.config_file
        if not default_path.exists():
            default_path.parent.mkdir(parents=True, exist_ok=True)
            with default_path.open("w") as f:
                yaml.dump(self._get_default_config(), f, default_flow_style=False)

    def load_config(self) -> None:
        """Reload configuration from all sources."""
        self._load_all_configs()

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value by section and key."""
        return self.config.get(section, {}).get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Get the entire configuration dictionary."""
        return self.config
    
    def set(self, section: str, key: str, value: Any) -> None:
        """Set a configuration value."""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save_config()
    
    def save_config(self) -> None:
        """Save configuration to the primary user config file."""
        # Save to the default user config file (last in the list)
        config_paths = self._get_config_paths()
        primary_config = config_paths[-1]
        
        # Ensure directory exists
        primary_config.parent.mkdir(parents=True, exist_ok=True)
        
        with primary_config.open("w") as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get information about configuration sources and current values."""
        info = {
            "sources": [str(path) for path in self.config_sources],
            "environment_overrides": [],
            "local_dev_config": Path.cwd() / ".linernodes.cfg",
            "custom_config_file": os.environ.get("LINERNODES_CONFIG_FILE"),
            "current_config": self.config
        }
        
        # Find environment variable overrides
        prefix = "LINERNODES_"
        for env_var, value in os.environ.items():
            if env_var.startswith(prefix):
                info["environment_overrides"].append(f"{env_var}={value}")
        
        return info
    
    def create_dev_config_template(self, file_path: Optional[Path] = None) -> Path:
        """Create a development configuration template."""
        if file_path is None:
            file_path = Path.cwd() / ".linernodes.cfg"
        
        # Create a template with common development overrides
        dev_config = {
            "mpd": {
                "music_dir": str(Path.cwd() / "test_music"),  # Local test music
                "use_custom_config": True
            },
            "knowledge_graph": {
                "db_path": str(Path.cwd() / "test_knowledge.db"),
                "cards_dir": str(Path.cwd() / "test_cards"),
                "auto_import": True  # Enable for development
            },
            "interfaces": {
                "web_port": 8501,
                "mcp_port": 8000,
                "graph_explorer_port": 8502
            },
            "musicbrainz": {
                "rate_limit": 0.5  # Faster for development
            }
        }
        
        with file_path.open("w") as f:
            f.write("# LinerNodes Development Configuration\n")
            f.write("# This file overrides default settings for local development\n")
            f.write("# Add to .gitignore to keep your local settings private\n\n")
            yaml.dump(dev_config, f, default_flow_style=False)
        
        return file_path
