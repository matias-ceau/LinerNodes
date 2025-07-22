# LinerNodes Database Schema Design

## Overview

LinerNodes uses SQLite as its internal database to maintain an authoritative, source-agnostic music collection. This document outlines the database schema designed to handle multiple music sources while maintaining MusicBrainz integration and rich relationship mapping.

## Core Tables

### Artists
Primary entity for musicians, bands, composers, and other musical persons/groups.

```sql
CREATE TABLE artists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mbid TEXT UNIQUE,  -- MusicBrainz ID for canonical reference
    name TEXT NOT NULL,
    sort_name TEXT,    -- For alphabetical sorting (e.g., "Beatles, The")
    type TEXT,         -- Person, Group, Orchestra, Choir, Character, Other
    disambiguation TEXT,
    begin_date DATE,
    end_date DATE,
    country TEXT,      -- ISO country code
    bio_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Albums
Central entity representing releases/albums (physical or digital collections).

```sql
CREATE TABLE albums (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mbid TEXT UNIQUE,  -- MusicBrainz Release ID
    title TEXT NOT NULL,
    artist_credit TEXT, -- How the artist should be credited
    release_date DATE,
    release_date_precision TEXT, -- year, month, day
    type TEXT,         -- Album, Single, EP, Compilation, Soundtrack, etc.
    status TEXT,       -- Official, Promotion, Bootleg, Pseudo-Release
    barcode TEXT,
    total_tracks INTEGER,
    total_discs INTEGER DEFAULT 1,
    cover_art_url TEXT,
    cover_art_local_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Tracks
Individual recordings/songs with comprehensive metadata.

```sql
CREATE TABLE tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mbid TEXT UNIQUE,  -- MusicBrainz Recording ID
    title TEXT NOT NULL,
    artist_credit TEXT,
    album_id INTEGER,
    track_number INTEGER,
    disc_number INTEGER DEFAULT 1,
    duration_ms INTEGER, -- Duration in milliseconds
    isrc TEXT,         -- International Standard Recording Code
    
    -- Audio properties
    bitrate INTEGER,
    sample_rate INTEGER,
    file_format TEXT,  -- mp3, flac, m4a, etc.
    
    -- Metadata
    genre TEXT,        -- Primary genre
    year INTEGER,      -- Recording year (may differ from release year)
    bpm INTEGER,       -- Beats per minute
    key_signature TEXT, -- Musical key
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
);
```

### Sources
Tracks where music files/streams can be accessed.

```sql
CREATE TABLE sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER NOT NULL,
    source_type TEXT NOT NULL, -- local, spotify, s3, google_drive, etc.
    source_id TEXT NOT NULL,   -- File path, Spotify URI, S3 key, etc.
    source_url TEXT,           -- Full URL if applicable
    source_metadata JSON,      -- Source-specific metadata
    quality TEXT,              -- lossless, high, medium, low
    availability TEXT,         -- available, unavailable, restricted
    last_verified TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
    UNIQUE(track_id, source_type, source_id)
);
```

### Labels
Record labels and publishers.

```sql
CREATE TABLE labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mbid TEXT UNIQUE,
    name TEXT NOT NULL,
    type TEXT,         -- Original Production, Bootleg Production, Reissue Production, etc.
    country TEXT,
    begin_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Genres
Hierarchical genre classification.

```sql
CREATE TABLE genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    parent_id INTEGER,  -- For genre hierarchy (Jazz -> Bebop)
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_id) REFERENCES genres(id)
);
```

## Relationship Tables

### Artist-Album Relationships

```sql
CREATE TABLE artist_albums (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_id INTEGER NOT NULL,
    album_id INTEGER NOT NULL,
    role TEXT DEFAULT 'primary',  -- primary, featured, composer, producer, etc.
    order_position INTEGER DEFAULT 0,
    
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE,
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
    UNIQUE(artist_id, album_id, role)
);
```

### Artist-Track Relationships

```sql
CREATE TABLE artist_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_id INTEGER NOT NULL,
    track_id INTEGER NOT NULL,
    role TEXT DEFAULT 'primary',  -- primary, featured, composer, performer, etc.
    instrument TEXT,              -- if performer role
    order_position INTEGER DEFAULT 0,
    
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE,
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
    UNIQUE(artist_id, track_id, role, instrument)
);
```

### Album-Label Relationships

```sql
CREATE TABLE album_labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    album_id INTEGER NOT NULL,
    label_id INTEGER NOT NULL,
    catalog_number TEXT,
    
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
    FOREIGN KEY (label_id) REFERENCES labels(id) ON DELETE CASCADE,
    UNIQUE(album_id, label_id, catalog_number)
);
```

### Track-Genre Relationships

```sql
CREATE TABLE track_genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    confidence REAL DEFAULT 1.0, -- How confident we are in this genre assignment (0.0-1.0)
    
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE,
    UNIQUE(track_id, genre_id)
);
```

## User Data Tables

### Playlists

```sql
CREATE TABLE playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    type TEXT DEFAULT 'user', -- user, smart, imported_spotify, etc.
    rules JSON,               -- For smart playlists
    total_tracks INTEGER DEFAULT 0,
    total_duration_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Playlist Tracks

```sql
CREATE TABLE playlist_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id INTEGER NOT NULL,
    track_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
    UNIQUE(playlist_id, track_id, position)
);
```

### Playback History

```sql
CREATE TABLE playback_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER NOT NULL,
    source_id INTEGER,        -- Which source was used
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_played_ms INTEGER, -- How much was actually played
    completed BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE SET NULL
);
```

### User Ratings & Tags

```sql
CREATE TABLE track_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
    UNIQUE(track_id)  -- One rating per track
);

CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    color TEXT,  -- Hex color for UI display
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE track_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    UNIQUE(track_id, tag_id)
);
```

## Metadata & System Tables

### MusicBrainz Cache

```sql
CREATE TABLE musicbrainz_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL, -- release, recording, artist, label
    mbid TEXT NOT NULL,
    data JSON NOT NULL,        -- Full MusicBrainz response
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    
    UNIQUE(entity_type, mbid)
);
```

### Import Jobs

```sql
CREATE TABLE import_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,
    source_path TEXT NOT NULL,
    status TEXT DEFAULT 'pending', -- pending, running, completed, failed
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Indexes for Performance

```sql
-- Primary search indexes
CREATE INDEX idx_artists_name ON artists(name);
CREATE INDEX idx_albums_title ON albums(title);
CREATE INDEX idx_tracks_title ON tracks(title);
CREATE INDEX idx_tracks_album ON tracks(album_id);

-- MusicBrainz ID indexes
CREATE INDEX idx_artists_mbid ON artists(mbid);
CREATE INDEX idx_albums_mbid ON albums(mbid);
CREATE INDEX idx_tracks_mbid ON tracks(mbid);

-- Source lookup indexes
CREATE INDEX idx_sources_track ON sources(track_id);
CREATE INDEX idx_sources_type ON sources(source_type);
CREATE INDEX idx_sources_availability ON sources(availability);

-- Relationship indexes
CREATE INDEX idx_artist_albums_artist ON artist_albums(artist_id);
CREATE INDEX idx_artist_albums_album ON artist_albums(album_id);
CREATE INDEX idx_artist_tracks_artist ON artist_tracks(artist_id);
CREATE INDEX idx_artist_tracks_track ON artist_tracks(track_id);

-- User data indexes
CREATE INDEX idx_playback_history_track ON playback_history(track_id);
CREATE INDEX idx_playback_history_played_at ON playback_history(played_at);
CREATE INDEX idx_playlist_tracks_playlist ON playlist_tracks(playlist_id);
CREATE INDEX idx_playlist_tracks_position ON playlist_tracks(playlist_id, position);
```

## Views for Common Queries

### Complete Track Information

```sql
CREATE VIEW track_details AS
SELECT 
    t.id,
    t.title,
    t.artist_credit,
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
GROUP BY t.id;
```

### Album with Tracks

```sql
CREATE VIEW album_details AS
SELECT 
    a.*,
    COUNT(t.id) as actual_track_count,
    SUM(t.duration_ms) as total_duration_ms,
    GROUP_CONCAT(DISTINCT ar.name) as artists
FROM albums a
LEFT JOIN tracks t ON a.id = t.album_id  
LEFT JOIN artist_albums aa ON a.id = aa.album_id
LEFT JOIN artists ar ON aa.artist_id = ar.id
GROUP BY a.id;
```

## Data Flow and Synchronization

1. **Import Process**: 
   - Scan source → Extract basic metadata → Query MusicBrainz → Store enriched data
   - Handle conflicts through smart deduplication based on MBID, audio fingerprints, or metadata similarity

2. **Source Management**:
   - Track availability per source
   - Periodic verification of source accessibility
   - Automatic failover between sources for playback

3. **Knowledge Graph Generation**:
   - Relationships automatically created through shared entities
   - Genre hierarchies maintained for intelligent classification
   - Collaborative filtering based on user behavior

This schema supports SQLite's capabilities while remaining extensible to PostgreSQL for larger deployments. The JSON fields provide flexibility for source-specific metadata without schema changes.