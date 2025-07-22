"""
Local file system source implementation.
Scans directories for music files and extracts metadata.
"""

import os
from pathlib import Path
from typing import List, Iterator, Optional, Dict, Any, Set
import mimetypes

try:
    import mutagen
    from mutagen.id3 import ID3NoHeaderError
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

from .base import LocalSource, SourceTrack, source_registry


class LocalFileSource(LocalSource):
    """Local file system music source."""
    
    # Supported audio formats
    SUPPORTED_EXTENSIONS = {
        '.mp3', '.flac', '.ogg', '.m4a', '.aac', '.wav', '.wma', '.opus'
    }
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.music_dirs = config.get('music_dirs', [])
        if isinstance(self.music_dirs, str):
            self.music_dirs = [self.music_dirs]
        
        # Expand paths
        self.music_dirs = [Path(os.path.expanduser(path)) for path in self.music_dirs]
        
        # Scan options
        self.recursive = config.get('recursive', True)
        self.follow_symlinks = config.get('follow_symlinks', True)
        self.include_extensions = set(config.get('include_extensions', []))
        self.exclude_extensions = set(config.get('exclude_extensions', []))
        
        if not MUTAGEN_AVAILABLE:
            self.logger.warning("Mutagen not available - metadata extraction will be limited")
    
    def is_available(self) -> bool:
        """Check if at least one music directory is accessible."""
        return any(path.exists() and path.is_dir() for path in self.music_dirs)
    
    def scan_tracks(self) -> Iterator[SourceTrack]:
        """Scan all configured directories for music files."""
        processed_files = set()
        
        for music_dir in self.music_dirs:
            if not music_dir.exists():
                self.logger.warning(f"Music directory does not exist: {music_dir}")
                continue
            
            self.logger.info(f"Scanning directory: {music_dir}")
            
            try:
                yield from self._scan_directory(music_dir, processed_files)
            except Exception as e:
                self.logger.error(f"Error scanning directory {music_dir}: {e}")
    
    def _scan_directory(self, directory: Path, processed_files: Set[str]) -> Iterator[SourceTrack]:
        """Recursively scan a directory for music files."""
        try:
            if self.recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for file_path in directory.glob(pattern):
                # Skip if already processed (handles duplicate paths)
                file_key = str(file_path.resolve())
                if file_key in processed_files:
                    continue
                
                # Skip directories
                if file_path.is_dir():
                    continue
                
                # Skip symlinks if configured
                if file_path.is_symlink() and not self.follow_symlinks:
                    continue
                
                # Check if it's a music file
                if self._is_music_file(file_path):
                    processed_files.add(file_key)
                    
                    try:
                        track = self._extract_track_metadata(file_path)
                        if track:
                            yield track
                    except Exception as e:
                        self.logger.error(f"Error processing file {file_path}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {e}")
    
    def _is_music_file(self, file_path: Path) -> bool:
        """Check if a file is a supported music file."""
        extension = file_path.suffix.lower()
        
        # Check custom include/exclude lists first
        if self.include_extensions and extension not in self.include_extensions:
            return False
        
        if self.exclude_extensions and extension in self.exclude_extensions:
            return False
        
        # Check supported extensions
        if extension in self.SUPPORTED_EXTENSIONS:
            return True
        
        # Check MIME type as fallback
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and mime_type.startswith('audio/'):
            return True
        
        return False
    
    def _extract_track_metadata(self, file_path: Path) -> Optional[SourceTrack]:
        """Extract metadata from a music file."""
        try:
            # Basic file information
            stat = file_path.stat()
            
            track = SourceTrack(
                title=file_path.stem,  # Default to filename
                source_type=self.source_type,
                source_id=str(file_path),
                source_url=file_path.as_uri(),
                format=file_path.suffix[1:].lower(),
                source_metadata={
                    'file_size': stat.st_size,
                    'modified_time': stat.st_mtime,
                }
            )
            
            # Extract metadata using mutagen if available
            if MUTAGEN_AVAILABLE:
                self._extract_mutagen_metadata(file_path, track)
            else:
                # Fallback: try to extract from directory structure
                self._extract_directory_metadata(file_path, track)
            
            # Determine quality from file format and bitrate
            self._determine_quality(track)
            
            return track
            
        except Exception as e:
            self.logger.error(f"Error extracting metadata from {file_path}: {e}")
            return None
    
    def _extract_mutagen_metadata(self, file_path: Path, track: SourceTrack):
        """Extract metadata using mutagen library."""
        try:
            audio_file = mutagen.File(str(file_path))
            if audio_file is None:
                return
            
            # Duration
            if hasattr(audio_file, 'info') and hasattr(audio_file.info, 'length'):
                track.duration_ms = int(audio_file.info.length * 1000)
            
            # Audio properties
            if hasattr(audio_file, 'info'):
                info = audio_file.info
                track.source_metadata.update({
                    'bitrate': getattr(info, 'bitrate', None),
                    'sample_rate': getattr(info, 'sample_rate', None),
                    'channels': getattr(info, 'channels', None),
                })
            
            # Tag mapping for different formats
            tag_mappings = {
                'title': ['TIT2', 'TITLE', '\\xa9nam'],
                'artist': ['TPE1', 'ARTIST', 'ALBUMARTIST', '\\xa9ART'],
                'album': ['TALB', 'ALBUM', '\\xa9alb'],
                'track_number': ['TRCK', 'TRACKNUMBER', 'trkn'],
                'disc_number': ['TPOS', 'DISCNUMBER', 'disk'],
                'genre': ['TCON', 'GENRE', '\\xa9gen'],
                'year': ['TDRC', 'DATE', 'YEAR', '\\xa9day'],
            }
            
            # Extract tags
            for field, possible_keys in tag_mappings.items():
                value = self._get_tag_value(audio_file, possible_keys)
                if value:
                    if field in ['track_number', 'disc_number']:
                        # Handle track/disc numbers (might be "1/10" format)
                        try:
                            if '/' in str(value):
                                value = int(str(value).split('/')[0])
                            else:
                                value = int(value)
                            setattr(track, field, value)
                        except (ValueError, TypeError):
                            pass
                    elif field == 'year':
                        # Extract year from date
                        try:
                            year_str = str(value)
                            if '-' in year_str:
                                year_str = year_str.split('-')[0]
                            track.year = int(year_str[:4])
                        except (ValueError, TypeError):
                            pass
                    else:
                        setattr(track, field, str(value))
            
        except (ID3NoHeaderError, Exception) as e:
            self.logger.debug(f"Could not read metadata from {file_path}: {e}")
            # Fall back to directory-based extraction
            self._extract_directory_metadata(file_path, track)
    
    def _get_tag_value(self, audio_file, possible_keys: List[str]):
        """Get tag value trying multiple possible keys."""
        if not audio_file.tags:
            return None
        
        for key in possible_keys:
            if key in audio_file.tags:
                value = audio_file.tags[key]
                if isinstance(value, list) and value:
                    return value[0]
                return value
        
        return None
    
    def _extract_directory_metadata(self, file_path: Path, track: SourceTrack):
        """Extract metadata from directory structure as fallback."""
        parts = file_path.parts
        
        # Try to parse from directory structure
        # Common patterns: /Artist/Album/Track.ext or /Artist - Album/Track.ext
        if len(parts) >= 3:
            # Assume last 2 directories are artist and album
            potential_artist = parts[-3]
            potential_album = parts[-2]
            
            # Clean up common separators
            if ' - ' in potential_artist:
                potential_artist = potential_artist.split(' - ')[0]
            
            track.artist = potential_artist
            track.album = potential_album
        
        # Try to extract track number from filename
        filename = file_path.stem
        if filename and filename[0].isdigit():
            try:
                # Look for patterns like "01 - Title" or "01. Title"
                for sep in [' - ', '. ', ' ']:
                    if sep in filename:
                        track_num_str = filename.split(sep)[0]
                        if track_num_str.isdigit():
                            track.track_number = int(track_num_str)
                            # Extract title after the separator
                            title = filename.split(sep, 1)[1]
                            track.title = title
                            break
            except (ValueError, IndexError):
                pass
    
    def _determine_quality(self, track: SourceTrack):
        """Determine audio quality based on format and bitrate."""
        format_lower = track.format.lower() if track.format else ''
        bitrate = track.source_metadata.get('bitrate')
        
        # Lossless formats
        if format_lower in ['flac', 'wav', 'aiff', 'ape', 'wv']:
            track.quality = 'lossless'
        elif bitrate:
            # Bitrate-based quality for lossy formats
            if bitrate >= 320:
                track.quality = 'high'
            elif bitrate >= 192:
                track.quality = 'medium'
            else:
                track.quality = 'low'
        else:
            # Unknown quality
            track.quality = 'unknown'
    
    def get_track_stream_url(self, source_id: str) -> Optional[str]:
        """Return file:// URL for local files."""
        path = Path(source_id)
        if path.exists() and path.is_file():
            return path.as_uri()
        return None
    
    def get_directories_summary(self) -> Dict[str, Any]:
        """Get summary information about configured directories."""
        summary = {
            'directories': [],
            'total_files': 0,
            'total_size': 0,
        }
        
        for music_dir in self.music_dirs:
            dir_info = {
                'path': str(music_dir),
                'exists': music_dir.exists(),
                'file_count': 0,
                'size_bytes': 0,
            }
            
            if music_dir.exists():
                try:
                    for file_path in music_dir.rglob('*') if self.recursive else music_dir.glob('*'):
                        if file_path.is_file() and self._is_music_file(file_path):
                            dir_info['file_count'] += 1
                            dir_info['size_bytes'] += file_path.stat().st_size
                except Exception as e:
                    dir_info['error'] = str(e)
            
            summary['directories'].append(dir_info)
            summary['total_files'] += dir_info['file_count']
            summary['total_size'] += dir_info['size_bytes']
        
        return summary


# Register the local file source
source_registry.register_source_class('local', LocalFileSource)