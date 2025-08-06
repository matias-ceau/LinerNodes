"""
Centralized source management for LinerNodes.
Handles discovery, import, and synchronization across all music sources.
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from .base import MusicSource, SourceStatus, source_registry
from ..backend.database.models import DatabaseManager
from ..config.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class SourceManager:
    """Manages all music sources and coordinates database imports."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, 
                 db_manager: Optional[DatabaseManager] = None):
        self.config_manager = config_manager or ConfigManager()
        self.db_manager = db_manager or DatabaseManager()
        self.sources: Dict[str, MusicSource] = {}
        self._load_sources_from_config()
    
    def _load_sources_from_config(self):
        """Load and initialize sources from configuration."""
        try:
            sources_config = self.config_manager.get_all().get('sources', {})
            
            for source_type, type_config in sources_config.items():
                if isinstance(type_config, dict):
                    for source_name, source_config in type_config.items():
                        if isinstance(source_config, dict):
                            try:
                                self._create_source(source_type, source_name, source_config)
                            except Exception as e:
                                logger.error(f"Failed to create source {source_name}: {e}")
                
        except Exception as e:
            logger.error(f"Error loading sources from config: {e}")
    
    def _create_source(self, source_type: str, source_name: str, config: Dict[str, Any]):
        """Create a source instance."""
        try:
            # Handle special case for local sources with multiple directories
            if source_type == 'local' and 'music_dirs' in config:
                full_name = f"{source_type}_{source_name}"
                source = source_registry.create_source(source_type, full_name, config)
                self.sources[full_name] = source
                logger.info(f"Created source: {full_name}")
            else:
                full_name = f"{source_type}_{source_name}"
                source = source_registry.create_source(source_type, full_name, config)
                self.sources[full_name] = source
                logger.info(f"Created source: {full_name}")
                
        except Exception as e:
            logger.error(f"Failed to create source {source_name} of type {source_type}: {e}")
    
    def get_all_sources(self) -> List[MusicSource]:
        """Get all registered sources."""
        return list(self.sources.values())
    
    def get_source_by_name(self, name: str) -> Optional[MusicSource]:
        """Get a specific source by name."""
        return self.sources.get(name)
    
    def get_sources_by_type(self, source_type: str) -> List[MusicSource]:
        """Get all sources of a specific type."""
        return [source for source in self.sources.values() 
                if source.source_type == source_type]
    
    def get_source_statuses(self) -> List[SourceStatus]:
        """Get status for all sources."""
        statuses = []
        for source in self.sources.values():
            try:
                status = source.get_status()
                statuses.append(status)
            except Exception as e:
                logger.error(f"Error getting status for source {source.name}: {e}")
                statuses.append(SourceStatus(
                    name=source.name,
                    type=source.source_type,
                    available=False,
                    error_message=str(e)
                ))
        return statuses
    
    def scan_all_sources(self) -> Dict[str, Any]:
        """Scan all sources for new content without importing."""
        results = {
            'scanned_sources': 0,
            'total_tracks_found': 0,
            'sources': {}
        }
        
        for source_name, source in self.sources.items():
            logger.info(f"Scanning source: {source_name}")
            
            try:
                if not source.is_available():
                    results['sources'][source_name] = {
                        'status': 'unavailable',
                        'tracks_found': 0,
                        'error': 'Source not available'
                    }
                    continue
                
                track_count = 0
                scan_start = datetime.now()
                
                # Count tracks without storing them
                for track in source.scan_tracks():
                    track_count += 1
                    
                    # Log progress every 1000 tracks
                    if track_count % 1000 == 0:
                        logger.info(f"Scanned {track_count} tracks from {source_name}")
                
                scan_duration = (datetime.now() - scan_start).total_seconds()
                
                results['sources'][source_name] = {
                    'status': 'success',
                    'tracks_found': track_count,
                    'scan_duration': scan_duration
                }
                
                results['scanned_sources'] += 1
                results['total_tracks_found'] += track_count
                
            except Exception as e:
                logger.error(f"Error scanning source {source_name}: {e}")
                results['sources'][source_name] = {
                    'status': 'error',
                    'tracks_found': 0,
                    'error': str(e)
                }
        
        return results
    
    def import_all_sources(self) -> Dict[str, Any]:
        """Import tracks from all sources into the database."""
        results = {
            'imported_sources': 0,
            'total_tracks_imported': 0,
            'total_tracks_skipped': 0,
            'total_errors': 0,
            'sources': {}
        }
        
        for source_name, source in self.sources.items():
            source_results = self.import_source(source_name)
            results['sources'][source_name] = source_results
            
            if source_results['status'] == 'success':
                results['imported_sources'] += 1
                results['total_tracks_imported'] += source_results['tracks_imported']
                results['total_tracks_skipped'] += source_results['tracks_skipped']
            
            results['total_errors'] += source_results.get('error_count', 0)
        
        return results
    
    def import_source(self, source_name: str) -> Dict[str, Any]:
        """Import tracks from a specific source."""
        if source_name not in self.sources:
            return {
                'status': 'error',
                'error': f'Source {source_name} not found'
            }
        
        source = self.sources[source_name]
        logger.info(f"Importing from source: {source_name}")
        
        try:
            if not source.is_available():
                return {
                    'status': 'error',
                    'error': 'Source not available'
                }
            
            import_start = datetime.now()
            tracks_imported = 0
            tracks_skipped = 0
            error_count = 0
            
            for track in source.scan_tracks():
                try:
                    # Check if track already exists
                    if self._track_exists(track):
                        tracks_skipped += 1
                        continue
                    
                    # Import track
                    self.db_manager.import_track_from_source(
                        track_data=track.to_dict(),
                        source_data=track.to_source_dict()
                    )
                    
                    tracks_imported += 1
                    
                    # Log progress
                    if (tracks_imported + tracks_skipped) % 100 == 0:
                        logger.info(f"Processed {tracks_imported + tracks_skipped} tracks "
                                  f"from {source_name} ({tracks_imported} imported)")
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error importing track {track.title}: {e}")
                    
                    # Stop if too many errors
                    if error_count > 100:
                        logger.error(f"Too many errors importing from {source_name}, stopping")
                        break
            
            import_duration = (datetime.now() - import_start).total_seconds()
            
            return {
                'status': 'success',
                'tracks_imported': tracks_imported,
                'tracks_skipped': tracks_skipped,
                'error_count': error_count,
                'import_duration': import_duration
            }
            
        except Exception as e:
            logger.error(f"Error importing from source {source_name}: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _track_exists(self, track) -> bool:
        """Check if a track already exists in the database."""
        # Simple existence check - could be made more sophisticated
        with self.db_manager.db.connection() as conn:
            cursor = conn.execute(
                """SELECT COUNT(*) FROM sources 
                   WHERE source_type = ? AND source_id = ?""",
                (track.source_type, track.source_id)
            )
            return cursor.fetchone()[0] > 0
    
    def sync_source(self, source_name: str) -> Dict[str, Any]:
        """Synchronize a source (update existing, add new, mark unavailable)."""
        if source_name not in self.sources:
            return {
                'status': 'error',
                'error': f'Source {source_name} not found'
            }
        
        source = self.sources[source_name]
        logger.info(f"Syncing source: {source_name}")
        
        try:
            # Get existing tracks from this source
            with self.db_manager.db.connection() as conn:
                cursor = conn.execute(
                    "SELECT source_id FROM sources WHERE source_type = ?",
                    (source.source_type,)
                )
                existing_source_ids = {row[0] for row in cursor.fetchall()}
            
            # Scan current tracks
            current_source_ids = set()
            added = 0
            updated = 0
            
            for track in source.scan_tracks():
                current_source_ids.add(track.source_id)
                
                if track.source_id not in existing_source_ids:
                    # New track
                    self.db_manager.import_track_from_source(
                        track_data=track.to_dict(),
                        source_data=track.to_source_dict()
                    )
                    added += 1
                else:
                    # Update existing (could implement smart updating here)
                    updated += 1
            
            # Mark missing tracks as unavailable
            missing_source_ids = existing_source_ids - current_source_ids
            removed = len(missing_source_ids)
            
            if missing_source_ids:
                with self.db_manager.db.connection() as conn:
                    placeholders = ','.join('?' * len(missing_source_ids))
                    conn.execute(
                        f"""UPDATE sources SET availability = 'unavailable' 
                            WHERE source_type = ? AND source_id IN ({placeholders})""",
                        [source.source_type] + list(missing_source_ids)
                    )
            
            return {
                'status': 'success',
                'tracks_added': added,
                'tracks_updated': updated,
                'tracks_removed': removed
            }
            
        except Exception as e:
            logger.error(f"Error syncing source {source_name}: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of all sources."""
        statuses = self.get_source_statuses()
        db_stats = self.db_manager.get_stats()
        
        available_sources = [s for s in statuses if s.available]
        
        return {
            'total_sources': len(statuses),
            'available_sources': len(available_sources),
            'source_types': list(set(s.type for s in statuses)),
            'database_stats': db_stats,
            'sources': statuses
        }