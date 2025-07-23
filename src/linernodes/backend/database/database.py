"""
Internal SQLite database manager for LinerNodes.
Serves as the authoritative source of truth for music metadata across all sources.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from contextlib import contextmanager

import os

# XDG fallback without external dependency
def xdg_data_home():
    """Get XDG data home directory with fallback."""
    return os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))


logger = logging.getLogger(__name__)


class LinerDatabase:
    """Internal SQLite database for music metadata and relationships."""
    
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            # Default to XDG data directory
            data_dir = Path(xdg_data_home()) / "linernodes"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "music.db"
        
        self.db_path = Path(db_path)
        self._ensure_database()
    
    def _ensure_database(self):
        """Create database and tables if they don't exist."""
        with self.connection() as conn:
            self._create_tables(conn)
            self._create_indexes(conn)
            self._create_views(conn)
    
    @contextmanager
    def connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        conn.execute("PRAGMA journal_mode = WAL")  # Enable WAL mode for concurrent access
        conn.execute("PRAGMA synchronous = NORMAL")  # Faster writes while maintaining safety
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _create_tables(self, conn: sqlite3.Connection):
        """Create all database tables."""
        
        # Artists table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS artists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mbid TEXT UNIQUE,
                name TEXT NOT NULL,
                sort_name TEXT,
                type TEXT,
                disambiguation TEXT,
                begin_date DATE,
                end_date DATE,
                country TEXT,
                bio_summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Albums table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS albums (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mbid TEXT UNIQUE,
                title TEXT NOT NULL,
                artist_credit TEXT,
                release_date DATE,
                release_date_precision TEXT,
                type TEXT,
                status TEXT,
                barcode TEXT,
                total_tracks INTEGER,
                total_discs INTEGER DEFAULT 1,
                cover_art_url TEXT,
                cover_art_local_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tracks table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mbid TEXT UNIQUE,
                title TEXT NOT NULL,
                artist_credit TEXT,
                album_id INTEGER,
                track_number INTEGER,
                disc_number INTEGER DEFAULT 1,
                duration_ms INTEGER,
                isrc TEXT,
                bitrate INTEGER,
                sample_rate INTEGER,
                file_format TEXT,
                genre TEXT,
                year INTEGER,
                bpm INTEGER,
                key_signature TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
            )
        """)
        
        # Sources table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id INTEGER NOT NULL,
                source_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                source_url TEXT,
                source_metadata TEXT,  -- JSON as TEXT
                quality TEXT,
                availability TEXT DEFAULT 'available',
                last_verified TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
                UNIQUE(track_id, source_type, source_id)
            )
        """)
        
        # Labels table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mbid TEXT UNIQUE,
                name TEXT NOT NULL,
                type TEXT,
                country TEXT,
                begin_date DATE,
                end_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Genres table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS genres (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                parent_id INTEGER,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES genres(id)
            )
        """)
        
        # Relationship tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS artist_albums (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artist_id INTEGER NOT NULL,
                album_id INTEGER NOT NULL,
                role TEXT DEFAULT 'primary',
                order_position INTEGER DEFAULT 0,
                FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE,
                FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
                UNIQUE(artist_id, album_id, role)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS artist_tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artist_id INTEGER NOT NULL,
                track_id INTEGER NOT NULL,
                role TEXT DEFAULT 'primary',
                instrument TEXT,
                order_position INTEGER DEFAULT 0,
                FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE,
                FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
                UNIQUE(artist_id, track_id, role, instrument)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS album_labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                album_id INTEGER NOT NULL,
                label_id INTEGER NOT NULL,
                catalog_number TEXT,
                FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
                FOREIGN KEY (label_id) REFERENCES labels(id) ON DELETE CASCADE,
                UNIQUE(album_id, label_id, catalog_number)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS track_genres (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id INTEGER NOT NULL,
                genre_id INTEGER NOT NULL,
                confidence REAL DEFAULT 1.0,
                FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
                FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE,
                UNIQUE(track_id, genre_id)
            )
        """)
        
        # User data tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                type TEXT DEFAULT 'user',
                rules TEXT,  -- JSON as TEXT
                total_tracks INTEGER DEFAULT 0,
                total_duration_ms INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS playlist_tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_id INTEGER NOT NULL,
                track_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
                FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
                UNIQUE(playlist_id, track_id, position)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS playback_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id INTEGER NOT NULL,
                source_id INTEGER,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration_played_ms INTEGER,
                completed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
                FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE SET NULL
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS track_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id INTEGER NOT NULL,
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
                UNIQUE(track_id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS track_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
                UNIQUE(track_id, tag_id)
            )
        """)
        
        # System tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS musicbrainz_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                mbid TEXT NOT NULL,
                data TEXT NOT NULL,  -- JSON as TEXT
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                UNIQUE(entity_type, mbid)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS import_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL,
                source_path TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                total_items INTEGER DEFAULT 0,
                processed_items INTEGER DEFAULT 0,
                error_message TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
    def _create_indexes(self, conn: sqlite3.Connection):
        """Create performance indexes."""
        indexes = [
            # Primary search indexes
            "CREATE INDEX IF NOT EXISTS idx_artists_name ON artists(name)",
            "CREATE INDEX IF NOT EXISTS idx_albums_title ON albums(title)",
            "CREATE INDEX IF NOT EXISTS idx_albums_artist_credit ON albums(artist_credit)",
            "CREATE INDEX IF NOT EXISTS idx_tracks_title ON tracks(title)",
            "CREATE INDEX IF NOT EXISTS idx_tracks_album ON tracks(album_id)",
            "CREATE INDEX IF NOT EXISTS idx_tracks_artist_credit ON tracks(artist_credit)",
            
            # MusicBrainz ID indexes
            "CREATE INDEX IF NOT EXISTS idx_artists_mbid ON artists(mbid)",
            "CREATE INDEX IF NOT EXISTS idx_albums_mbid ON albums(mbid)",
            "CREATE INDEX IF NOT EXISTS idx_tracks_mbid ON tracks(mbid)",
            
            # Source lookup indexes
            "CREATE INDEX IF NOT EXISTS idx_sources_track ON sources(track_id)",
            "CREATE INDEX IF NOT EXISTS idx_sources_type ON sources(source_type)",
            "CREATE INDEX IF NOT EXISTS idx_sources_availability ON sources(availability)",
            
            # Relationship indexes
            "CREATE INDEX IF NOT EXISTS idx_artist_albums_artist ON artist_albums(artist_id)",
            "CREATE INDEX IF NOT EXISTS idx_artist_albums_album ON artist_albums(album_id)",
            "CREATE INDEX IF NOT EXISTS idx_artist_tracks_artist ON artist_tracks(artist_id)",
            "CREATE INDEX IF NOT EXISTS idx_artist_tracks_track ON artist_tracks(track_id)",
            
            # User data indexes
            "CREATE INDEX IF NOT EXISTS idx_playback_history_track ON playback_history(track_id)",
            "CREATE INDEX IF NOT EXISTS idx_playback_history_played_at ON playback_history(played_at)",
            "CREATE INDEX IF NOT EXISTS idx_playlist_tracks_playlist ON playlist_tracks(playlist_id)",
            "CREATE INDEX IF NOT EXISTS idx_playlist_tracks_position ON playlist_tracks(playlist_id, position)",
        ]
        
        for index in indexes:
            conn.execute(index)
    
    def _create_views(self, conn: sqlite3.Connection):
        """Create useful views for common queries."""
        
        # Complete track information view
        conn.execute("""
            CREATE VIEW IF NOT EXISTS track_details AS
            SELECT 
                t.id,
                t.title,
                t.artist_credit,
                t.album_id,
                a.title as album_title,
                a.release_date,
                t.track_number,
                t.disc_number,
                t.duration_ms,
                t.genre,
                t.year,
                GROUP_CONCAT(s.source_type) as available_sources,
                COUNT(s.id) as source_count
            FROM tracks t
            LEFT JOIN albums a ON t.album_id = a.id
            LEFT JOIN sources s ON t.id = s.track_id AND s.availability = 'available'
            GROUP BY t.id
        """)
        
        # Album with tracks view
        conn.execute("""
            CREATE VIEW IF NOT EXISTS album_details AS
            SELECT 
                a.*,
                COUNT(t.id) as actual_track_count,
                SUM(t.duration_ms) as total_duration_ms,
                GROUP_CONCAT(DISTINCT ar.name) as artists
            FROM albums a
            LEFT JOIN tracks t ON a.id = t.album_id  
            LEFT JOIN artist_albums aa ON a.id = aa.album_id
            LEFT JOIN artists ar ON aa.artist_id = ar.id
            GROUP BY a.id
        """)
        
        # Graph relationships view for fast graph building with smart sampling
        conn.execute("""
            CREATE VIEW IF NOT EXISTS graph_relationships AS
            -- Album to Artist relationships (prioritize albums with more tracks)
            SELECT 
                'album' as source_type,
                'album_' || a.id as source_id,
                a.title as source_name,
                'artist' as target_type,
                'artist_' || a.artist_credit as target_id,
                a.artist_credit as target_name,
                'performed_by' as relationship_type,
                COALESCE((SELECT COUNT(*) FROM tracks t WHERE t.album_id = a.id), 0) as weight
            FROM albums a 
            WHERE a.artist_credit IS NOT NULL
            
            UNION ALL
            
            -- Track to Album relationships  
            SELECT 
                'track' as source_type,
                'track_' || t.id as source_id,
                t.title as source_name,
                'album' as target_type,
                'album_' || t.album_id as target_id,
                a.title as target_name,
                'belongs_to' as relationship_type,
                1 as weight
            FROM tracks t
            JOIN albums a ON t.album_id = a.id
            
            UNION ALL
            
            -- Track to Artist relationships (through album)
            SELECT 
                'track' as source_type,
                'track_' || t.id as source_id,
                t.title as source_name,
                'artist' as target_type,
                'artist_' || a.artist_credit as target_id,
                a.artist_credit as target_name,
                'performed_by' as relationship_type,
                1 as weight
            FROM tracks t
            JOIN albums a ON t.album_id = a.id
            WHERE a.artist_credit IS NOT NULL
        """)
    
    # CRUD operations for core entities
    
    def add_artist(self, name: str, **kwargs) -> int:
        """Add an artist to the database."""
        with self.connection() as conn:
            cursor = conn.execute(
                """INSERT INTO artists (name, sort_name, type, disambiguation, 
                   begin_date, end_date, country, bio_summary, mbid)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    name,
                    kwargs.get('sort_name'),
                    kwargs.get('type'),
                    kwargs.get('disambiguation'),
                    kwargs.get('begin_date'),
                    kwargs.get('end_date'),
                    kwargs.get('country'),
                    kwargs.get('bio_summary'),
                    kwargs.get('mbid')
                )
            )
            return cursor.lastrowid
    
    def add_album(self, title: str, **kwargs) -> int:
        """Add an album to the database."""
        with self.connection() as conn:
            cursor = conn.execute(
                """INSERT INTO albums (title, artist_credit, release_date, 
                   release_date_precision, type, status, barcode, total_tracks, 
                   total_discs, cover_art_url, cover_art_local_path, mbid)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    title,
                    kwargs.get('artist_credit'),
                    kwargs.get('release_date'),
                    kwargs.get('release_date_precision'),
                    kwargs.get('type'),
                    kwargs.get('status'),
                    kwargs.get('barcode'),
                    kwargs.get('total_tracks'),
                    kwargs.get('total_discs', 1),
                    kwargs.get('cover_art_url'),
                    kwargs.get('cover_art_local_path'),
                    kwargs.get('mbid')
                )
            )
            return cursor.lastrowid
    
    def add_track(self, title: str, album_id: int, **kwargs) -> int:
        """Add a track to the database."""
        with self.connection() as conn:
            cursor = conn.execute(
                """INSERT INTO tracks (title, artist_credit, album_id, track_number,
                   disc_number, duration_ms, isrc, bitrate, sample_rate, file_format,
                   genre, year, bpm, key_signature, mbid)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    title,
                    kwargs.get('artist_credit'),
                    album_id,
                    kwargs.get('track_number'),
                    kwargs.get('disc_number', 1),
                    kwargs.get('duration_ms'),
                    kwargs.get('isrc'),
                    kwargs.get('bitrate'),
                    kwargs.get('sample_rate'),
                    kwargs.get('file_format'),
                    kwargs.get('genre'),
                    kwargs.get('year'),
                    kwargs.get('bpm'),
                    kwargs.get('key_signature'),
                    kwargs.get('mbid')
                )
            )
            return cursor.lastrowid
    
    def add_source(self, track_id: int, source_type: str, source_id: str, **kwargs) -> int:
        """Add a source reference for a track."""
        with self.connection() as conn:
            metadata_json = json.dumps(kwargs.get('source_metadata', {}))
            cursor = conn.execute(
                """INSERT OR REPLACE INTO sources 
                   (track_id, source_type, source_id, source_url, source_metadata, 
                    quality, availability, last_verified)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    track_id,
                    source_type,
                    source_id,
                    kwargs.get('source_url'),
                    metadata_json,
                    kwargs.get('quality'),
                    kwargs.get('availability', 'available'),
                    kwargs.get('last_verified')
                )
            )
            return cursor.lastrowid
    
    # Search and query methods
    
    def search_tracks(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search tracks by title, artist, or album."""
        with self.connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM track_details 
                   WHERE title LIKE ? OR artist_credit LIKE ? OR album_title LIKE ?
                   ORDER BY title LIMIT ?""",
                (f"%{query}%", f"%{query}%", f"%{query}%", limit)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_albums(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all albums with details."""
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM album_details ORDER BY title LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_track_sources(self, track_id: int) -> List[Dict[str, Any]]:
        """Get all sources for a specific track."""
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM sources WHERE track_id = ? AND availability = 'available'",
                (track_id,)
            )
            sources = []
            for row in cursor.fetchall():
                source = dict(row)
                # Parse JSON metadata
                if source['source_metadata']:
                    try:
                        source['source_metadata'] = json.loads(source['source_metadata'])
                    except json.JSONDecodeError:
                        source['source_metadata'] = {}
                sources.append(source)
            return sources
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        with self.connection() as conn:
            stats = {}
            
            # Count each table
            tables = ['artists', 'albums', 'tracks', 'sources', 'playlists']
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            
            # Available tracks (with sources)
            cursor = conn.execute(
                "SELECT COUNT(DISTINCT track_id) FROM sources WHERE availability = 'available'"
            )
            stats['available_tracks'] = cursor.fetchone()[0]
            
            return stats
    
    def vacuum_database(self):
        """Optimize database performance."""
        with self.connection() as conn:
            conn.execute("VACUUM")
            conn.execute("ANALYZE")