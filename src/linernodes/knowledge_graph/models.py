from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class EntityType(Enum):
    """Core entity types in the music knowledge graph."""
    ALBUM = "album"
    ARTIST = "artist" 
    PERSON = "person"
    GENRE = "genre"
    LABEL = "label"
    RECORDING = "recording"
    WORK = "work"
    RELEASE_GROUP = "release_group"
    MEDIUM = "medium"

class RelationshipType(Enum):
    """Relationship types between entities."""
    # Album relationships
    PERFORMED_BY = "performed_by"
    PRODUCED_BY = "produced_by"
    RECORDED_AT = "recorded_at"
    RELEASED_BY = "released_by"
    HAS_GENRE = "has_genre"
    CONTAINS_RECORDING = "contains_recording"
    
    # Artist relationships
    MEMBER_OF = "member_of"
    COLLABORATED_WITH = "collaborated_with"
    INFLUENCED_BY = "influenced_by"
    SIMILAR_TO = "similar_to"
    
    # Genre relationships
    SUBGENRE_OF = "subgenre_of"
    RELATED_TO = "related_to"
    
    # Work relationships
    COMPOSITION_OF = "composition_of"
    ARRANGEMENT_OF = "arrangement_of"
    COVER_OF = "cover_of"

@dataclass
class BaseEntity:
    """Base class for all knowledge graph entities."""
    id: Optional[str]
    entity_type: EntityType
    name: str
    mbid: Optional[str] = None  # MusicBrainz ID
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    metadata: Dict[str, Any] = {}
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

@dataclass
class Album(BaseEntity):
    """Central entity representing an album/release (physical medium equivalent)."""
    artist_credit: str = ""
    release_date: Optional[datetime] = None
    label: Optional[str] = None
    catalog_number: Optional[str] = None
    barcode: Optional[str] = None
    country: Optional[str] = None
    status: str = "Official"  # Official, Promotion, Bootleg, etc.
    packaging: Optional[str] = None  # CD, Vinyl, Digital, etc.
    total_tracks: int = 0
    total_length: Optional[int] = None  # in seconds
    genres: List[str] = []
    recordings: List[str] = []
    
    def __post_init__(self):
        super().__post_init__()
        self.entity_type = EntityType.ALBUM

@dataclass  
class Artist(BaseEntity):
    """Artist/band entity."""
    sort_name: str = ""
    disambiguation: str = ""
    artist_type: str = "Person"  # Person, Group, Orchestra, Choir, Character, Other
    gender: Optional[str] = None
    country: Optional[str] = None
    begin_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ended: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        self.entity_type = EntityType.ARTIST

@dataclass
class Genre(BaseEntity):
    """Genre/style entity."""
    description: str = ""
    parent_genres: List[str] = []
    child_genres: List[str] = []
    
    def __post_init__(self):
        super().__post_init__()
        self.entity_type = EntityType.GENRE

@dataclass
class Recording(BaseEntity):
    """Individual recording/track entity."""
    length: Optional[int] = None  # in milliseconds
    disambiguation: str = ""
    video: bool = False
    file_path: Optional[str] = None
    track_number: Optional[int] = None
    disc_number: Optional[int] = None
    album_id: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.entity_type = EntityType.RECORDING

@dataclass
class Person(BaseEntity):
    """Individual person (musician, producer, etc.)."""
    birth_date: Optional[datetime] = None
    death_date: Optional[datetime] = None
    gender: Optional[str] = None
    country: Optional[str] = None
    instruments: List[str] = []
    roles: List[str] = []
    
    def __post_init__(self):
        super().__post_init__()
        self.entity_type = EntityType.PERSON

@dataclass
class Label(BaseEntity):
    """Record label entity."""
    label_code: Optional[str] = None
    country: Optional[str] = None
    begin_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    label_type: str = "Original Production"
    
    def __post_init__(self):
        super().__post_init__()
        self.entity_type = EntityType.LABEL

@dataclass
class Relationship:
    """Relationship between two entities."""
    id: Optional[str]
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    attributes: Dict[str, Any] = {}
    begin_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime = datetime.now()
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

class EntityFactory:
    """Factory for creating entities with proper validation."""

    @staticmethod
    def _coerce_entity_type(value: object | None, default_et: EntityType) -> EntityType:
        """
        Accept either an EntityType or a string; return a valid EntityType.
        Falls back to default_et for None or invalid strings.
        """
        if isinstance(value, EntityType):
            return value
        if isinstance(value, str):
            try:
                return EntityType(value)
            except Exception:
                return default_et
        return default_et

    @staticmethod
    def create_album(name: str, **kwargs) -> Album:
        """Create a new Album entity."""
        entity_type_val: object | None = kwargs.pop('entity_type', None)
        entity_type = EntityFactory._coerce_entity_type(entity_type_val, EntityType.ALBUM)
        return Album(
            id=kwargs.get('id'),
            name=name,
            entity_type=entity_type,
            **kwargs
        )
    
    @staticmethod
    def create_artist(name: str, **kwargs) -> Artist:
        """Create a new Artist entity."""
        entity_type_val: object | None = kwargs.pop('entity_type', None)
        entity_type = EntityFactory._coerce_entity_type(entity_type_val, EntityType.ARTIST)
        return Artist(
            id=kwargs.get('id'),
            name=name,
            sort_name=kwargs.get('sort_name', name),
            entity_type=entity_type,
            **kwargs
        )
    
    @staticmethod
    def create_genre(name: str, **kwargs) -> Genre:
        """Create a new Genre entity."""
        entity_type_val: object | None = kwargs.pop('entity_type', None)
        entity_type = EntityFactory._coerce_entity_type(entity_type_val, EntityType.GENRE)
        return Genre(
            id=kwargs.get('id'),
            name=name,
            entity_type=entity_type,
            **kwargs
        )
    
    @staticmethod
    def create_recording(name: str, **kwargs) -> Recording:
        """Create a new Recording entity."""
        entity_type_val: object | None = kwargs.pop('entity_type', None)
        entity_type = EntityFactory._coerce_entity_type(entity_type_val, EntityType.RECORDING)
        return Recording(
            id=kwargs.get('id'),
            name=name,
            entity_type=entity_type,
            **kwargs
        )
    
    @staticmethod
    def create_person(name: str, **kwargs) -> Person:
        """Create a new Person entity."""
        entity_type_val: object | None = kwargs.pop('entity_type', None)
        entity_type = EntityFactory._coerce_entity_type(entity_type_val, EntityType.PERSON)
        return Person(
            id=kwargs.get('id'),
            name=name,
            entity_type=entity_type,
            **kwargs
        )
    
    @staticmethod
    def create_label(name: str, **kwargs) -> Label:
        """Create a new Label entity."""
        entity_type_val: object | None = kwargs.pop('entity_type', None)
        entity_type = EntityFactory._coerce_entity_type(entity_type_val, EntityType.LABEL)
        return Label(
            id=kwargs.get('id'),
            name=name,
            entity_type=entity_type,
            **kwargs
        )