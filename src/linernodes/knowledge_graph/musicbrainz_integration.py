import musicbrainzngs as mb
from typing import Optional, List, Dict, Any
from datetime import datetime
import time

from .models import (
    Album, Artist, Recording, Label, Person, Genre, Relationship,
    EntityType, RelationshipType, EntityFactory
)
from .graph_db import KnowledgeGraphDB

class MusicBrainzIntegration:
    """Integration with MusicBrainz to populate the knowledge graph."""
    
    def __init__(self, kg_db: KnowledgeGraphDB, user_agent: str = "LinerNodes/1.0"):
        """Initialize MusicBrainz integration."""
        self.kg_db = kg_db
        
        # Set up MusicBrainz client
        mb.set_useragent("LinerNodes", "1.0", "https://github.com/your-repo/linernodes")
        mb.set_rate_limit(limit_or_interval=1.0, new_requests=1)
        
    def search_and_import_release(self, query: str, limit: int = 10) -> List[Album]:
        """Search for releases and import them into the knowledge graph."""
        try:
            # Search for releases
            search_results = mb.search_releases(query=query, limit=limit)
            
            imported_albums = []
            for release_data in search_results.get('release-list', []):
                album = self.import_release_by_mbid(release_data['id'])
                if album:
                    imported_albums.append(album)
                time.sleep(1)  # Rate limiting
            
            return imported_albums
            
        except Exception as e:
            print(f"Error searching MusicBrainz releases: {e}")
            return []
    
    def import_release_by_mbid(self, mbid: str) -> Optional[Album]:
        """Import a specific release by MusicBrainz ID."""
        try:
            # Check if already imported
            existing = self._find_entity_by_mbid(mbid)
            if existing:
                return existing
            
            # Get detailed release information
            release_data = mb.get_release_by_id(
                mbid, 
                includes=['artists', 'recordings', 'labels', 'genres', 'media']
            )['release']
            
            # Create Album entity
            album = self._create_album_from_mb_data(release_data)
            self.kg_db.add_entity(album)
            
            # Import related artists
            self._import_release_artists(release_data, album)
            
            # Import recordings/tracks
            self._import_release_recordings(release_data, album)
            
            # Import label information
            self._import_release_labels(release_data, album)
            
            # Import genres/tags
            self._import_release_genres(release_data, album)
            
            return album
            
        except Exception as e:
            print(f"Error importing release {mbid}: {e}")
            return None
    
    def import_artist_by_mbid(self, mbid: str) -> Optional[Artist]:
        """Import a specific artist by MusicBrainz ID."""
        try:
            # Check if already imported
            existing = self._find_entity_by_mbid(mbid)
            if existing:
                return existing
            
            # Get detailed artist information
            artist_data = mb.get_artist_by_id(
                mbid,
                includes=['releases', 'genres', 'artist-rels']
            )['artist']
            
            # Create Artist entity
            artist = self._create_artist_from_mb_data(artist_data)
            self.kg_db.add_entity(artist)
            
            # Import artist relationships
            self._import_artist_relationships(artist_data, artist)
            
            return artist
            
        except Exception as e:
            print(f"Error importing artist {mbid}: {e}")
            return None
    
    def _create_album_from_mb_data(self, release_data: Dict[str, Any]) -> Album:
        """Create Album entity from MusicBrainz release data."""
        
        # Parse release date
        release_date = None
        if release_data.get('date'):
            try:
                date_str = release_data['date']
                if len(date_str) == 4:  # Year only
                    release_date = datetime.strptime(date_str, '%Y')
                elif len(date_str) == 7:  # Year-month
                    release_date = datetime.strptime(date_str, '%Y-%m')
                else:  # Full date
                    release_date = datetime.strptime(date_str, '%Y-%m-%d')
            except:
                pass
        
        # Get artist credit
        artist_credit = ""
        if release_data.get('artist-credit'):
            artist_names = []
            for credit in release_data['artist-credit']:
                if isinstance(credit, dict) and 'artist' in credit:
                    artist_names.append(credit['artist']['name'])
                elif isinstance(credit, str):
                    artist_names.append(credit)
            artist_credit = "".join(artist_names)
        
        # Extract other metadata
        label_info = ""
        catalog_number = ""
        if release_data.get('label-info-list'):
            label_data = release_data['label-info-list'][0]
            if label_data.get('label'):
                label_info = label_data['label'].get('name', '')
            catalog_number = label_data.get('catalog-number', '')
        
        # Count tracks
        total_tracks = 0
        if release_data.get('medium-list'):
            for medium in release_data['medium-list']:
                if medium.get('track-list'):
                    total_tracks += len(medium['track-list'])
        
        album = EntityFactory.create_album(
            name=release_data.get('title', 'Unknown Album'),
            id=None,  # Will be auto-generated
            mbid=release_data['id'],
            artist_credit=artist_credit,
            release_date=release_date,
            label=label_info,
            catalog_number=catalog_number,
            barcode=release_data.get('barcode'),
            country=release_data.get('country'),
            status=release_data.get('status', 'Official'),
            total_tracks=total_tracks,
            packaging=release_data.get('packaging'),
            genres=[],  # Will be populated separately
            recordings=[]  # Will be populated separately
        )
        
        return album
    
    def _create_artist_from_mb_data(self, artist_data: Dict[str, Any]) -> Artist:
        """Create Artist entity from MusicBrainz artist data."""
        
        # Parse dates
        begin_date = None
        end_date = None
        
        if artist_data.get('life-span'):
            life_span = artist_data['life-span']
            if life_span.get('begin'):
                try:
                    begin_date = datetime.strptime(life_span['begin'], '%Y-%m-%d')
                except:
                    try:
                        begin_date = datetime.strptime(life_span['begin'], '%Y')
                    except:
                        pass
            
            if life_span.get('end'):
                try:
                    end_date = datetime.strptime(life_span['end'], '%Y-%m-%d')
                except:
                    try:
                        end_date = datetime.strptime(life_span['end'], '%Y')
                    except:
                        pass
        
        artist = EntityFactory.create_artist(
            name=artist_data.get('name', 'Unknown Artist'),
            mbid=artist_data['id'],
            sort_name=artist_data.get('sort-name', artist_data.get('name', '')),
            disambiguation=artist_data.get('disambiguation', ''),
            artist_type=artist_data.get('type', 'Person'),
            gender=artist_data.get('gender'),
            country=artist_data.get('country'),
            begin_date=begin_date,
            end_date=end_date,
            ended=artist_data.get('life-span', {}).get('ended', False)
        )
        
        return artist
    
    def _import_release_artists(self, release_data: Dict[str, Any], album: Album):
        """Import artists associated with a release."""
        if not release_data.get('artist-credit'):
            return
        
        for credit in release_data['artist-credit']:
            if isinstance(credit, dict) and 'artist' in credit:
                artist_data = credit['artist']
                
                # Check if artist already exists
                artist = self._find_entity_by_mbid(artist_data['id'])
                if not artist:
                    # Create basic artist entity (full import can be done separately)
                    artist = EntityFactory.create_artist(
                        name=artist_data['name'],
                        mbid=artist_data['id'],
                        sort_name=artist_data.get('sort-name', artist_data['name'])
                    )
                    self.kg_db.add_entity(artist)
                
                # Create relationship
                relationship = Relationship(
                    id=None,  # Auto-generated
                    source_id=album.id,
                    target_id=artist.id,
                    relationship_type=RelationshipType.PERFORMED_BY
                )
                self.kg_db.add_relationship(relationship)
    
    def _import_release_recordings(self, release_data: Dict[str, Any], album: Album):
        """Import recordings/tracks from a release."""
        if not release_data.get('medium-list'):
            return
        
        track_recordings = []
        
        for medium in release_data['medium-list']:
            if not medium.get('track-list'):
                continue
                
            for track_data in medium['track-list']:
                if not track_data.get('recording'):
                    continue
                
                recording_data = track_data['recording']
                
                # Create recording entity
                recording = EntityFactory.create_recording(
                    name=recording_data.get('title', 'Unknown Track'),
                    mbid=recording_data['id'],
                    length=recording_data.get('length'),  # in milliseconds
                    track_number=track_data.get('position'),
                    album_id=album.id
                )
                
                self.kg_db.add_entity(recording)
                track_recordings.append(recording.id)
                
                # Create relationship
                relationship = Relationship(
                    id=None,
                    source_id=album.id,
                    target_id=recording.id,
                    relationship_type=RelationshipType.CONTAINS_RECORDING
                )
                self.kg_db.add_relationship(relationship)
        
        # Update album with recording IDs
        album.recordings = track_recordings
        self.kg_db.add_entity(album)  # Update existing
    
    def _import_release_labels(self, release_data: Dict[str, Any], album: Album):
        """Import label information from a release."""
        if not release_data.get('label-info-list'):
            return
        
        for label_info in release_data['label-info-list']:
            if not label_info.get('label'):
                continue
                
            label_data = label_info['label']
            
            # Check if label already exists
            label = self._find_entity_by_mbid(label_data['id'])
            if not label:
                # Create label entity
                label = EntityFactory.create_label(
                    name=label_data['name'],
                    mbid=label_data['id'],
                    label_code=label_data.get('label-code')
                )
                self.kg_db.add_entity(label)
            
            # Create relationship
            relationship = Relationship(
                id=None,
                source_id=album.id,
                target_id=label.id,
                relationship_type=RelationshipType.RELEASED_BY
            )
            self.kg_db.add_relationship(relationship)
    
    def _import_release_genres(self, release_data: Dict[str, Any], album: Album):
        """Import genre/tag information from a release."""
        genres = []
        
        # Get genres from tags
        if release_data.get('tag-list'):
            for tag in release_data['tag-list']:
                genre_name = tag['name'].title()
                genres.append(genre_name)
                
                # Create genre entity if not exists
                existing_genres = self.kg_db.search_entities(
                    genre_name, EntityType.GENRE
                )
                
                if not existing_genres:
                    genre = EntityFactory.create_genre(name=genre_name)
                    self.kg_db.add_entity(genre)
                    
                    # Create relationship
                    relationship = Relationship(
                        id=None,
                        source_id=album.id,
                        target_id=genre.id,
                        relationship_type=RelationshipType.HAS_GENRE
                    )
                    self.kg_db.add_relationship(relationship)
        
        # Update album genres
        album.genres = genres
        self.kg_db.add_entity(album)  # Update existing
    
    def _import_artist_relationships(self, artist_data: Dict[str, Any], artist: Artist):
        """Import artist relationship information."""
        # This would handle band memberships, collaborations, etc.
        # Simplified implementation for now
        pass
    
    def _find_entity_by_mbid(self, mbid: str):
        """Find an existing entity by MusicBrainz ID."""
        try:
            result = self.kg_db.conn.execute(
                "SELECT * FROM entities WHERE mbid = ?",
                (mbid,)
            ).fetchone()
            
            if result:
                return self.kg_db._row_to_entity(result)
        except:
            pass
        return None

    def bulk_import_from_collection(self, file_paths: List[str]) -> Dict[str, int]:
        """Import multiple audio files using their metadata."""
        stats = {"albums": 0, "artists": 0, "recordings": 0, "errors": 0}
        
        # This would integrate with beets or direct metadata reading
        # to extract MusicBrainz IDs from file tags and import accordingly
        # Simplified implementation for now
        
        for file_path in file_paths:
            try:
                # Extract metadata from file
                # Search/import via MusicBrainz
                # Update stats
                pass
            except Exception as e:
                stats["errors"] += 1
                print(f"Error importing {file_path}: {e}")
        
        return stats