"""
Database models for LinerNodes internal database.
Provides high-level interfaces to the SQLite database operations.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pathlib import Path
import pickle
import hashlib
import os

from .database import LinerDatabase


@dataclass
class Artist:
    """Artist entity model representing musicians, bands, and music creators.
    
    This class represents individual artists or groups with comprehensive metadata
    including biographical information, MusicBrainz integration, and database
    persistence capabilities.
    
    Attributes:
        name (str): Primary artist name as displayed
        id (Optional[int]): Database primary key, auto-assigned
        mbid (Optional[str]): MusicBrainz ID for canonical identification
        sort_name (Optional[str]): Name formatted for alphabetical sorting
        type (Optional[str]): Artist type (Person, Group, Orchestra, etc.)
        disambiguation (Optional[str]): Clarification for similar named artists
        begin_date (Optional[date]): Career start or birth date
        end_date (Optional[date]): Career end or death date
        country (Optional[str]): Country of origin or activity
        bio_summary (Optional[str]): Brief biographical description
        created_at (Optional[datetime]): Record creation timestamp
        updated_at (Optional[datetime]): Last modification timestamp
        
    Example:
        >>> artist = Artist(
        ...     name="Miles Davis",
        ...     sort_name="Davis, Miles", 
        ...     type="Person",
        ...     country="US",
        ...     begin_date=date(1926, 5, 26),
        ...     end_date=date(1991, 9, 28)
        ... )
        >>> artist_id = artist.save(database)
    """
    name: str
    id: Optional[int] = None
    mbid: Optional[str] = None
    sort_name: Optional[str] = None
    type: Optional[str] = None  # Person, Group, Orchestra, etc.
    disambiguation: Optional[str] = None
    begin_date: Optional[date] = None
    end_date: Optional[date] = None
    country: Optional[str] = None
    bio_summary: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def save(self, db: LinerDatabase) -> int:
        data = {k: v for k, v in asdict(self).items() if k not in ['id', 'created_at', 'updated_at'] and v is not None}
        self.id = db.add_artist(**data)
        return self.id


@dataclass
class Album:
    title: str
    id: Optional[int] = None
    mbid: Optional[str] = None
    artist_credit: Optional[str] = None
    release_date: Optional[date] = None
    release_date_precision: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    barcode: Optional[str] = None
    total_tracks: Optional[int] = None
    total_discs: Optional[int] = None
    cover_art_url: Optional[str] = None
    cover_art_local_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    actual_track_count: Optional[int] = None
    total_duration_ms: Optional[int] = None
    artists: List[str] = field(default_factory=list)
    
    def save(self, db: LinerDatabase) -> int:
        data = {k: v for k, v in asdict(self).items() if k not in ['id', 'created_at', 'updated_at', 'actual_track_count', 'total_duration_ms', 'artists'] and v is not None}
        self.id = db.add_album(**data)
        return self.id


@dataclass
class Track:
    title: str
    album_id: int
    id: Optional[int] = None
    mbid: Optional[str] = None
    artist_credit: Optional[str] = None
    track_number: Optional[int] = None
    disc_number: Optional[int] = None
    duration_ms: Optional[int] = None
    isrc: Optional[str] = None
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    file_format: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    bpm: Optional[int] = None
    key_signature: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Computed fields from joins
    album_title: Optional[str] = None
    release_date: Optional[date] = None
    available_sources: Optional[str] = None
    source_count: Optional[int] = None
    
    def save(self, db: LinerDatabase) -> int:
        """Save track to database."""
        data = {k: v for k, v in asdict(self).items() 
                if k not in ['id', 'created_at', 'updated_at', 'album_title', 
                            'release_date', 'available_sources', 'source_count'] and v is not None}
        self.id = db.add_track(**data)
        return self.id
    
    @property
    def duration_formatted(self) -> str:
        """Format duration as MM:SS."""
        if not self.duration_ms:
            return "0:00"
        minutes, seconds = divmod(self.duration_ms // 1000, 60)
        return f"{minutes}:{seconds:02d}"


@dataclass
class Source:
    """Source reference model."""
    track_id: int
    source_type: str  # local, spotify, s3, google_drive, etc.
    source_id: str    # file path, URI, etc.
    id: Optional[int] = None
    source_url: Optional[str] = None
    source_metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    quality: Optional[str] = None
    availability: str = 'available'
    last_verified: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    def save(self, db: LinerDatabase) -> int:
        data = {k: v for k, v in asdict(self).items() if k not in ['id', 'created_at'] and v is not None}
        self.id = db.add_source(**data)
        return self.id
    
    @property
    def is_local(self) -> bool:
        """Check if this is a local file source."""
        return self.source_type == 'local'
    
    @property
    def file_path(self) -> Optional[Path]:
        """Get file path for local sources."""
        if self.is_local:
            return Path(self.source_id)
        return None


@dataclass
class Genre:
    """Genre model."""
    name: str
    id: Optional[int] = None
    parent_id: Optional[int] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class Label:
    """Record label model."""
    name: str
    id: Optional[int] = None
    mbid: Optional[str] = None
    type: Optional[str] = None
    country: Optional[str] = None
    begin_date: Optional[date] = None
    end_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Playlist:
    """Playlist model."""
    name: str
    id: Optional[int] = None
    description: Optional[str] = None
    type: str = 'user'  # user, smart, imported_spotify, etc.
    rules: Optional[Dict[str, Any]] = None  # For smart playlists
    total_tracks: int = 0
    total_duration_ms: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DatabaseManager:
    """High-level database management interface."""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db = LinerDatabase(db_path)
        # Register automatic cache invalidation on data changes
        self.db.register_cache_invalidation_callback(self.invalidate_graph_cache)
    
    def search_music(self, query: str, limit: int = 50) -> List[Track]:
        """Search for tracks across the database."""
        results = self.db.search_tracks(query, limit)
        tracks = []
        for result in results:
            # Ensure album_id is provided, default to 0 if missing
            if 'album_id' not in result:
                result['album_id'] = 0
            tracks.append(Track(**result))
        return tracks
    
    def get_all_albums(self, limit: int = 100) -> List[Album]:
        """Get all albums with metadata."""
        results = self.db.get_albums(limit)
        return [Album(**result) for result in results]
    
    def get_unique_artists(self, limit: int = 100) -> List[str]:
        """Get unique artist names from the database."""
        with self.db.connection() as conn:
            cursor = conn.execute("""
                SELECT DISTINCT artist_credit 
                FROM tracks 
                WHERE artist_credit IS NOT NULL 
                ORDER BY artist_credit 
                LIMIT ?
            """, (limit,))
            return [row[0] for row in cursor.fetchall()]
    
    def get_track_by_id(self, track_id: int) -> Optional[Track]:
        """Get a specific track by ID."""
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM track_details WHERE id = ?", 
                (track_id,)
            )
            result = cursor.fetchone()
            return Track(**dict(result)) if result else None
    
    def get_album_tracks(self, album_id: int) -> List[Track]:
        """Get all tracks for an album."""
        with self.db.connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM track_details WHERE id IN 
                   (SELECT id FROM tracks WHERE album_id = ?)
                   ORDER BY disc_number, track_number""",
                (album_id,)
            )
            return [Track(**dict(row)) for row in cursor.fetchall()]
    
    def get_track_sources(self, track_id: int) -> List[Source]:
        """Get all sources for a track."""
        results = self.db.get_track_sources(track_id)
        return [Source(**result) for result in results]
    
    def get_graph_data_bulk(self, limit: int = 5000) -> Dict:
        """Get bulk graph data in single query - optimized for graph building."""
        with self.db.connection() as conn:
            # Single query to get all relationships using smart sampling
            cursor = conn.execute("""
                SELECT * FROM graph_relationships 
                ORDER BY weight DESC, relationship_type, source_name
                LIMIT ?
            """, (limit,))
            
            relationships = [dict(row) for row in cursor.fetchall()]
            
            # Extract unique nodes and edges efficiently
            nodes = {}
            edges = []
            
            for rel in relationships:
                # Add source node
                if rel['source_id'] not in nodes:
                    nodes[rel['source_id']] = {
                        'id': rel['source_id'],
                        'name': rel['source_name'][:50],  # Truncate for performance
                        'type': rel['source_type']
                    }
                
                # Add target node  
                if rel['target_id'] not in nodes:
                    nodes[rel['target_id']] = {
                        'id': rel['target_id'],
                        'name': rel['target_name'][:50],  # Truncate for performance
                        'type': rel['target_type']
                    }
                
                # Add edge
                edges.append({
                    'source': rel['source_id'],
                    'target': rel['target_id'],
                    'type': rel['relationship_type']
                })
            
            return {
                'nodes': list(nodes.values()),
                'edges': edges,
                'stats': {
                    'node_count': len(nodes),
                    'edge_count': len(edges),
                    'relationship_count': len(relationships)
                }
            }
    
    def get_relationships_batch(self, node_types: List[str] = None, limit: int = 10000) -> List[Dict]:
        """Get relationships in batch for specific node types."""
        with self.db.connection() as conn:
            if node_types:
                placeholders = ','.join(['?' for _ in node_types])
                query = f"""
                    SELECT * FROM graph_relationships 
                    WHERE source_type IN ({placeholders}) OR target_type IN ({placeholders})
                    ORDER BY relationship_type
                    LIMIT ?
                """
                params = node_types + node_types + [limit]
            else:
                query = """
                    SELECT * FROM graph_relationships 
                    ORDER BY relationship_type
                    LIMIT ?
                """
                params = [limit]
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_graph_cache_path(self) -> Path:
        """Get path for persistent graph cache."""
        cache_dir = Path.home() / ".cache" / "linernodes"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / "graph_cache.pkl"
    
    def get_database_fingerprint(self) -> str:
        """Get fingerprint of database state for cache invalidation."""
        with self.db.connection() as conn:
            # Get row counts for key tables
            tables_info = []
            for table in ['albums', 'tracks', 'artists']:
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    tables_info.append((table, count))
                except Exception:
                    tables_info.append((table, 0))
            
            # Add database file modification time
            db_stat = os.stat(self.db.db_path)
            fingerprint_data = {
                'tables': dict(tables_info),
                'db_mtime': db_stat.st_mtime,
                'db_size': db_stat.st_size
            }
            
            return hashlib.md5(str(fingerprint_data).encode()).hexdigest()
    
    def get_cached_graph_data(self, max_nodes: int = 5000) -> Optional[Dict]:
        """Get pre-computed graph data from persistent cache."""
        cache_path = self.get_graph_cache_path()
        
        if not cache_path.exists():
            return None
            
        try:
            with open(cache_path, 'rb') as f:
                cached = pickle.load(f)
            
            # Check if cache is still valid
            current_fingerprint = self.get_database_fingerprint()
            if cached.get('fingerprint') != current_fingerprint:
                return None  # Cache is stale
                
            # Check if cached data has enough nodes
            if cached.get('max_nodes', 0) < max_nodes:
                return None  # Need more nodes
                
            return cached.get('data')
            
        except Exception:
            # Cache corrupted, remove it
            cache_path.unlink(missing_ok=True)
            return None
    
    def cache_graph_data(self, data: Dict, max_nodes: int):
        """Store graph data in persistent cache."""
        cache_path = self.get_graph_cache_path()
        
        cached = {
            'data': data,
            'fingerprint': self.get_database_fingerprint(),
            'max_nodes': max_nodes,
            'created_at': datetime.now().isoformat()
        }
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(cached, f)
        except Exception as e:
            print(f"Warning: Could not cache graph data: {e}")
    
    def invalidate_graph_cache(self):
        """Invalidate the persistent graph cache."""
        cache_path = self.get_graph_cache_path()
        cache_path.unlink(missing_ok=True)
    
    def get_graph_data_bulk_cached(self, limit: int = 5000) -> Dict:
        """Get bulk graph data with persistent caching."""
        # Try to get from cache first
        cached_data = self.get_cached_graph_data(limit)
        if cached_data:
            return cached_data
        
        # Cache miss - compute and store
        data = self.get_graph_data_bulk(limit)
        self.cache_graph_data(data, limit)
        
        return data
    
    def find_or_create_artist(self, name: str, mbid: Optional[str] = None) -> Artist:
        """Find existing artist or create new one."""
        with self.db.connection() as conn:
            # Try to find by MBID first
            if mbid:
                cursor = conn.execute("SELECT * FROM artists WHERE mbid = ?", (mbid,))
                result = cursor.fetchone()
                if result:
                    return Artist(**dict(result))
            
            # Try to find by name
            cursor = conn.execute("SELECT * FROM artists WHERE name = ?", (name,))
            result = cursor.fetchone()
            if result:
                return Artist(**dict(result))
            
            # Create new artist
            artist = Artist(name=name, mbid=mbid)
            artist.save(self.db)
            return artist
    
    def find_or_create_album(self, title: str, artist_credit: str = "Unknown Artist", 
                           mbid: Optional[str] = None) -> Album:
        """Find existing album or create new one."""
        # Ensure we have a valid title
        if not title or title.strip() == "":
            title = "Unknown Album"
            
        with self.db.connection() as conn:
            # Try to find by MBID first
            if mbid:
                cursor = conn.execute("SELECT * FROM albums WHERE mbid = ?", (mbid,))
                result = cursor.fetchone()
                if result:
                    return Album(**dict(result))
            
            # Try to find by title and artist
            cursor = conn.execute(
                "SELECT * FROM albums WHERE title = ? AND artist_credit = ?", 
                (title, artist_credit)
            )
            result = cursor.fetchone()
            if result:
                return Album(**dict(result))
            
            # Create new album
            album = Album(title=title, artist_credit=artist_credit, mbid=mbid)
            album.save(self.db)
            return album
    
    def import_track_from_source(self, track_data: Dict[str, Any], 
                                source_data: Dict[str, Any]) -> Track:
        """Import a track with its source information."""
        # Find or create album
        album_title = track_data.get('album') or 'Unknown Album'
        artist_name = track_data.get('artist') or 'Unknown Artist'
        
        album = self.find_or_create_album(
            title=album_title,
            artist_credit=artist_name,
            mbid=track_data.get('album_mbid')
        )
        
        # Create track
        track = Track(
            title=track_data['title'],
            album_id=album.id,
            artist_credit=track_data.get('artist'),
            track_number=track_data.get('track_number'),
            disc_number=track_data.get('disc_number', 1),
            duration_ms=track_data.get('duration_ms'),
            genre=track_data.get('genre'),
            year=track_data.get('year'),
            file_format=track_data.get('format'),
            mbid=track_data.get('mbid')
        )
        track.save(self.db)
        
        # Add source
        source = Source(
            track_id=track.id,
            source_type=source_data['source_type'],
            source_id=source_data['source_id'],
            source_url=source_data.get('source_url'),
            source_metadata=source_data.get('metadata', {}),
            quality=source_data.get('quality')
        )
        source.save(self.db)
        
        return track
    
    def get_stats(self) -> Dict[str, Any]:
        stats = self.db.get_database_stats()
        
        if stats.get('tracks', 0) > 0:
            stats['coverage_percent'] = (stats.get('available_tracks', 0) / stats['tracks']) * 100
        else:
            stats['coverage_percent'] = 0.0
        
        return stats
    
    def vacuum_and_optimize(self):
        """Optimize database performance."""
        self.db.vacuum_database()