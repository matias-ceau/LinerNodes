"""Configuration - Multi-Source Configuration Management.

This module provides a flexible, hierarchical configuration system that supports
multiple configuration sources with clear precedence rules, type validation,
and XDG directory compliance.

## Configuration Hierarchy

Configuration is loaded from multiple sources with the following precedence
(highest to lowest):

1. **Environment Variables**: `LINERNODES_<SECTION>_<KEY>=value`
2. **Local Dev Config**: `.linernodes.cfg` in current directory
3. **Custom Config File**: Path specified by `LINERNODES_CONFIG_FILE`
4. **User Config**: `~/.config/linernodes/config.yaml`
5. **System Config**: `/etc/linernodes/config.yaml`
6. **Default Values**: Built-in defaults

## Configuration Structure

### Core Sections

#### MPD Section
```yaml
mpd:
  host: localhost
  port: 6600
  password: null
  music_dir: ~/Music
  auto_setup: true
  config_file: ~/.config/linernodes/mpd.conf
```

#### Database Section
```yaml
database:
  path: ~/.local/share/linernodes/music.db
  backup_enabled: true
  backup_interval: 3600  # seconds
  optimize_on_startup: false
```

#### Sources Section
```yaml
sources:
  local:
    main:
      music_dirs:
        - ~/Music
        - /mnt/music
      recursive: true
      follow_symlinks: false
      supported_formats: [mp3, flac, ogg, m4a, wav]
```

### Environment Variable Override

Any configuration value can be overridden using environment variables:

```bash
# Override MPD host
export LINERNODES_MPD_HOST=192.168.1.100

# Override database path
export LINERNODES_DATABASE_PATH=/tmp/test.db

# Override web interface port
export LINERNODES_INTERFACES_WEB_PORT=9000
```

## Usage Examples

```python
from linernodes.config import ConfigManager

# Initialize configuration
config = ConfigManager()

# Get configuration values
mpd_host = config.get('mpd', 'host')
music_dir = config.get('mpd', 'music_dir')
db_path = config.get('database', 'path')

# Get with default fallback
port = config.get('mpd', 'port', default=6600)

# Set configuration values
config.set('mpd', 'host', 'music-server.local')
config.save()  # Persist to user config file
```

## XDG Compliance

The configuration system follows XDG Base Directory specification:

- **Config**: `$XDG_CONFIG_HOME/linernodes/` (default: `~/.config/linernodes/`)
- **Data**: `$XDG_DATA_HOME/linernodes/` (default: `~/.local/share/linernodes/`)
- **State**: `$XDG_STATE_HOME/linernodes/` (default: `~/.local/state/linernodes/`)
- **Cache**: `$XDG_CACHE_HOME/linernodes/` (default: `~/.cache/linernodes/`)
"""

from .config_manager import ConfigManager

__all__ = ["ConfigManager"]