import pytest
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

from src.linernodes.knowledge_graph.models import (
    EntityType, RelationshipType, EntityFactory, Relationship
)
from src.linernodes.knowledge_graph.graph_db import KnowledgeGraphDB
from src.linernodes.knowledge_graph.markdown_cards import MarkdownCardGenerator


class TestEntityModels:
    """Test entity model classes."""
    
    def test_album_creation(self):
        """Test Album entity creation."""
        album = EntityFactory.create_album(
            name="Test Album",
            artist_credit="Test Artist",
            release_date=datetime(2023, 1, 1)
        )
        
        assert album.name == "Test Album"
        assert album.entity_type == EntityType.ALBUM
        assert album.artist_credit == "Test Artist"
        assert album.release_date == datetime(2023, 1, 1)
        assert isinstance(album.id, str)
        assert len(album.id) > 0
    
    def test_artist_creation(self):
        """Test Artist entity creation."""
        artist = EntityFactory.create_artist(
            name="Test Artist",
            artist_type="Person",
            country="US"
        )
        
        assert artist.name == "Test Artist"
        assert artist.entity_type == EntityType.ARTIST
        assert artist.artist_type == "Person"
        assert artist.country == "US"
        assert artist.sort_name == "Test Artist"
    
    def test_recording_creation(self):
        """Test Recording entity creation."""
        recording = EntityFactory.create_recording(
            name="Test Song",
            length=240000,  # 4 minutes in ms
            track_number=1
        )
        
        assert recording.name == "Test Song"
        assert recording.entity_type == EntityType.RECORDING
        assert recording.length == 240000
        assert recording.track_number == 1
    
    def test_genre_creation(self):
        """Test Genre entity creation."""
        genre = EntityFactory.create_genre(
            name="Rock",
            description="Rock music genre"
        )
        
        assert genre.name == "Rock"
        assert genre.entity_type == EntityType.GENRE
        assert genre.description == "Rock music genre"
        assert isinstance(genre.parent_genres, list)
        assert isinstance(genre.child_genres, list)


class TestKnowledgeGraphDB:
    """Test knowledge graph database operations."""
    
    def setup_method(self):
        """Set up test database."""
        self.db = KnowledgeGraphDB(":memory:")
    
    def test_add_and_get_album(self):
        """Test adding and retrieving album entities."""
        album = EntityFactory.create_album(
            name="Test Album",
            artist_credit="Test Artist"
        )
        
        # Add to database
        success = self.db.add_entity(album)
        assert success
        
        # Retrieve from database
        retrieved = self.db.get_entity(album.id)
        assert retrieved is not None
        assert retrieved.name == "Test Album"
        assert retrieved.entity_type == EntityType.ALBUM
        assert retrieved.artist_credit == "Test Artist"
    
    def test_search_entities(self):
        """Test entity search functionality."""
        # Add test entities
        album1 = EntityFactory.create_album(name="Rock Album")
        album2 = EntityFactory.create_album(name="Jazz Album")
        artist = EntityFactory.create_artist(name="Rock Star")
        
        self.db.add_entity(album1)
        self.db.add_entity(album2)
        self.db.add_entity(artist)
        
        # Search for "rock"
        results = self.db.search_entities("rock")
        assert len(results) >= 2  # Should find album and artist
        
        # Search by entity type
        album_results = self.db.search_entities("album", EntityType.ALBUM)
        assert len(album_results) == 2
        assert all(r.entity_type == EntityType.ALBUM for r in album_results)
    
    def test_relationships(self):
        """Test relationship creation and retrieval."""
        # Create entities
        album = EntityFactory.create_album(name="Test Album")
        artist = EntityFactory.create_artist(name="Test Artist")
        
        self.db.add_entity(album)
        self.db.add_entity(artist)
        
        # Create relationship
        relationship = Relationship(
            id=None,
            source_id=album.id,
            target_id=artist.id,
            relationship_type=RelationshipType.PERFORMED_BY
        )
        
        success = self.db.add_relationship(relationship)
        assert success
        
        # Get relationships
        album_rels = self.db.get_relationships(album.id)
        assert len(album_rels) == 1
        assert album_rels[0].relationship_type == RelationshipType.PERFORMED_BY
        
        artist_rels = self.db.get_relationships(artist.id)
        assert len(artist_rels) == 1
    
    def test_connected_entities(self):
        """Test getting connected entities."""
        # Create entities and relationships
        album = EntityFactory.create_album(name="Test Album")
        artist = EntityFactory.create_artist(name="Test Artist")
        genre = EntityFactory.create_genre(name="Rock")
        
        self.db.add_entity(album)
        self.db.add_entity(artist)
        self.db.add_entity(genre)
        
        # Add relationships
        rel1 = Relationship(
            id=None,
            source_id=album.id,
            target_id=artist.id,
            relationship_type=RelationshipType.PERFORMED_BY
        )
        
        rel2 = Relationship(
            id=None,
            source_id=album.id,
            target_id=genre.id,
            relationship_type=RelationshipType.HAS_GENRE
        )
        
        self.db.add_relationship(rel1)
        self.db.add_relationship(rel2)
        
        # Get connected entities
        connected = self.db.get_connected_entities(album.id)
        assert len(connected) == 2
        
        # Test filtering by relationship type
        artists = self.db.get_connected_entities(
            album.id, RelationshipType.PERFORMED_BY
        )
        assert len(artists) == 1
        assert artists[0].entity_type == EntityType.ARTIST


class TestMarkdownCards:
    """Test markdown card generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cards_dir = Path(self.temp_dir) / "cards"
        self.generator = MarkdownCardGenerator(self.cards_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_album_card_generation(self):
        """Test album markdown card generation."""
        album = EntityFactory.create_album(
            name="Test Album",
            artist_credit="Test Artist",
            release_date=datetime(2023, 1, 1),
            genres=["Rock", "Alternative"]
        )
        
        card_path = self.generator.generate_card(album)
        
        # Check that card was created
        assert card_path.exists()
        assert card_path.parent.name == "album"
        
        # Check card content
        content = card_path.read_text(encoding='utf-8')
        assert "Test Album" in content
        assert "Test Artist" in content
        assert "2023-01-01" in content
        assert "Rock" in content
        assert "Alternative" in content
        
        # Check YAML frontmatter
        lines = content.split('\n')
        assert lines[0] == "---"
        frontmatter_end = lines.index("---", 1)
        frontmatter = '\n'.join(lines[1:frontmatter_end])
        
        import yaml
        metadata = yaml.safe_load(frontmatter)
        assert metadata['name'] == "Test Album"
        assert metadata['entity_type'] == "album"
        assert metadata['artist_credit'] == "Test Artist"
        assert "Rock" in metadata['genres']
    
    def test_artist_card_generation(self):
        """Test artist markdown card generation."""
        artist = EntityFactory.create_artist(
            name="Test Artist",
            artist_type="Person",
            country="US",
            begin_date=datetime(1980, 1, 1)
        )
        
        card_path = self.generator.generate_card(artist)
        
        assert card_path.exists()
        assert card_path.parent.name == "artist"
        
        content = card_path.read_text(encoding='utf-8')
        assert "Test Artist" in content
        assert "Person" in content
        assert "US" in content
        assert "1980-01-01" in content
    
    def test_filename_sanitization(self):
        """Test filename sanitization for problematic names."""
        album = EntityFactory.create_album(
            name="Test/Album: With?Special*Characters"
        )
        
        card_path = self.generator.generate_card(album)
        assert card_path.exists()
        
        # Check that problematic characters were sanitized
        filename = card_path.name
        assert "/" not in filename
        assert ":" not in filename
        assert "?" not in filename
        assert "*" not in filename
    
    def test_card_exists_and_update(self):
        """Test checking for existing cards and updating them."""
        album = EntityFactory.create_album(name="Test Album")
        
        # Initially should not exist
        assert not self.generator.card_exists(album)
        
        # Generate card
        card_path = self.generator.generate_card(album)
        assert self.generator.card_exists(album)
        
        # Update should work
        album.artist_credit = "Updated Artist"
        updated_path = self.generator.update_card(album)
        
        assert updated_path == card_path
        content = card_path.read_text(encoding='utf-8')
        assert "Updated Artist" in content


class TestEntityFactory:
    """Test entity factory methods."""
    
    def test_create_person(self):
        """Test person entity creation."""
        person = EntityFactory.create_person(
            name="John Doe",
            instruments=["guitar", "vocals"],
            roles=["musician", "songwriter"]
        )
        
        assert person.name == "John Doe"
        assert person.entity_type == EntityType.PERSON
        assert "guitar" in person.instruments
        assert "musician" in person.roles
    
    def test_create_label(self):
        """Test label entity creation."""
        label = EntityFactory.create_label(
            name="Test Records",
            label_type="Original Production",
            country="US"
        )
        
        assert label.name == "Test Records"
        assert label.entity_type == EntityType.LABEL
        assert label.label_type == "Original Production"
        assert label.country == "US"


@pytest.fixture
def sample_entities():
    """Fixture providing sample entities for testing."""
    album = EntityFactory.create_album(
        name="Sample Album",
        artist_credit="Sample Artist"
    )
    
    artist = EntityFactory.create_artist(
        name="Sample Artist",
        artist_type="Person"
    )
    
    genre = EntityFactory.create_genre(
        name="Sample Genre",
        description="A sample music genre"
    )
    
    return {
        "album": album,
        "artist": artist,
        "genre": genre
    }


def test_entity_integration(sample_entities):
    """Integration test using sample entities."""
    db = KnowledgeGraphDB(":memory:")
    
    # Add entities
    for entity in sample_entities.values():
        success = db.add_entity(entity)
        assert success
    
    # Create relationships
    album = sample_entities["album"]
    artist = sample_entities["artist"]
    genre = sample_entities["genre"]
    
    rel1 = Relationship(
        id=None,
        source_id=album.id,
        target_id=artist.id,
        relationship_type=RelationshipType.PERFORMED_BY
    )
    
    rel2 = Relationship(
        id=None,
        source_id=album.id,
        target_id=genre.id,
        relationship_type=RelationshipType.HAS_GENRE
    )
    
    db.add_relationship(rel1)
    db.add_relationship(rel2)
    
    # Test queries
    albums = db.get_albums()
    assert len(albums) == 1
    assert albums[0].name == "Sample Album"
    
    # Test connected entities
    connected = db.get_connected_entities(album.id)
    assert len(connected) == 2
    
    entity_types = [e.entity_type for e in connected]
    assert EntityType.ARTIST in entity_types
    assert EntityType.GENRE in entity_types