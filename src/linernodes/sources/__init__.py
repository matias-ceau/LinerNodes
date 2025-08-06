"""Sources - Multi-Source Music Collection Management.

This module provides a flexible, extensible framework for managing music from
multiple sources including local files, streaming services, and cloud storage.

## Architecture

### Plugin-Based Design
The sources system uses a plugin architecture that allows easy addition of new
source types without modifying core functionality:

```python
class CustomSource(MusicSource):
    def scan_tracks(self) -> Iterator[SourceTrack]:
        # Implementation for custom source
        yield SourceTrack(title="...", source_path="custom://...")
        
# Register the new source type
source_registry.register("custom", CustomSource)
```

### Source Types

#### Local Files (`local_files.py`)
- Filesystem scanning with configurable depth
- Mutagen-based metadata extraction
- Support for multiple audio formats (MP3, FLAC, OGG, M4A, etc.)
- Symlink handling and duplicate detection
- Watch mode for real-time updates

#### Streaming Services (Future)
- Spotify integration with API access
- Apple Music library synchronization
- YouTube Music playlist import
- SoundCloud track discovery

#### Cloud Storage (Future)
- Google Drive music folders
- Dropbox synchronization
- Amazon S3 bucket scanning
- OneDrive integration

### Data Flow

1. **Discovery**: Sources scan their respective locations
2. **Extraction**: Metadata extracted using source-specific methods
3. **Normalization**: Data converted to common `SourceTrack` format
4. **Import**: Tracks imported into central database
5. **Synchronization**: Ongoing updates and availability tracking

## Core Components

### SourceTrack
Standardized representation of a track from any source:
- **Metadata**: Title, artist, album, genre, year, etc.
- **Technical**: Duration, bitrate, format, file size
- **Source**: Original location and access information
- **Availability**: Current status and last checked time

### MusicSource (Abstract Base)
Defines the interface all sources must implement:
- `scan_tracks()`: Discover and yield tracks
- `get_track_info()`: Retrieve detailed metadata
- `is_available()`: Check source accessibility
- `sync()`: Update existing tracks

### SourceManager
Coordinates multiple sources and manages import operations:
- Source registration and discovery
- Parallel scanning for performance
- Conflict resolution for duplicate tracks
- Progress tracking and error handling

## Configuration

Sources are configured through the main configuration system:

```yaml
sources:
  local:
    main:
      music_dirs: ["/home/user/Music", "/mnt/music"]
      recursive: true
      follow_symlinks: false
      watch_mode: true
  
  spotify:  # Future
    enabled: false
    client_id: "your_client_id"
    library_sync: true
```

## Usage Examples

```python
from linernodes.sources import SourceManager

# Initialize source manager
manager = SourceManager()

# Scan all configured sources
results = manager.scan_all_sources()
print(f"Found {results['total_tracks']} tracks")

# Import into database
import_results = manager.import_all_sources()
print(f"Imported {import_results['imported_tracks']} tracks")

# Check specific source
local_source = manager.get_source("local_main")
if local_source.is_available():
    tracks = list(local_source.scan_tracks())
```

## Performance Optimization

### Parallel Processing
- Multiple sources scanned concurrently
- Thread pools for I/O-intensive operations
- Progress tracking across parallel operations

### Incremental Updates
- Only scan changed files/directories
- Timestamp-based change detection
- Efficient database synchronization

### Caching
- Metadata caching for frequently accessed tracks
- Source availability caching
- Progressive loading for large collections
"""

from .base import MusicSource, SourceTrack, SourceStatus, source_registry
from .source_manager import SourceManager

# Import source implementations to register them
from . import local_files

__all__ = ['MusicSource', 'SourceTrack', 'SourceStatus', 'source_registry', 'SourceManager', 'local_files']