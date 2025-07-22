import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from .models import (
    BaseEntity, Album, Artist, Genre, Recording, Person, Label,
    EntityType
)

class MarkdownCardGenerator:
    """Generate markdown cards with YAML frontmatter for music entities."""
    
    def __init__(self, cards_dir: Optional[Path] = None):
        """Initialize the markdown card generator."""
        self.cards_dir = cards_dir or Path.home() / ".local/share/linernodes/cards"
        self.cards_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for each entity type
        for entity_type in EntityType:
            (self.cards_dir / entity_type.value).mkdir(exist_ok=True)
    
    def generate_card(self, entity: BaseEntity) -> Path:
        """Generate a markdown card for the given entity."""
        frontmatter = self._generate_frontmatter(entity)
        content = self._generate_content(entity)
        
        # Create filename (sanitized name)
        safe_name = self._sanitize_filename(entity.name)
        filename = f"{safe_name}.md"
        card_path = self.cards_dir / entity.entity_type.value / filename
        
        # Write the card
        with open(card_path, 'w', encoding='utf-8') as f:
            f.write("---\n")
            yaml.dump(frontmatter, f, default_flow_style=False, allow_unicode=True)
            f.write("---\n\n")
            f.write(content)
        
        return card_path
    
    def _generate_frontmatter(self, entity: BaseEntity) -> Dict[str, Any]:
        """Generate YAML frontmatter for entity."""
        frontmatter = {
            'id': entity.id,
            'entity_type': entity.entity_type.value,
            'name': entity.name,
            'created_at': entity.created_at.isoformat() if entity.created_at else None,
            'updated_at': entity.updated_at.isoformat() if entity.updated_at else None,
            'mbid': entity.mbid,
            'aliases': [],
            'tags': [entity.entity_type.value],
            'links': []
        }
        
        if isinstance(entity, Album):
            frontmatter.update({
                'artist_credit': entity.artist_credit,
                'release_date': entity.release_date.isoformat() if entity.release_date else None,
                'label': entity.label,
                'catalog_number': entity.catalog_number,
                'barcode': entity.barcode,
                'country': entity.country,
                'status': entity.status,
                'packaging': entity.packaging,
                'total_tracks': entity.total_tracks,
                'total_length_seconds': entity.total_length,
                'genres': entity.genres,
                'recordings': entity.recordings
            })
            frontmatter['tags'].extend(['album', 'release'])
            if entity.genres:
                frontmatter['tags'].extend(entity.genres)
        
        elif isinstance(entity, Artist):
            frontmatter.update({
                'sort_name': entity.sort_name,
                'disambiguation': entity.disambiguation,
                'artist_type': entity.artist_type,
                'gender': entity.gender,
                'country': entity.country,
                'begin_date': entity.begin_date.isoformat() if entity.begin_date else None,
                'end_date': entity.end_date.isoformat() if entity.end_date else None,
                'ended': entity.ended
            })
            frontmatter['tags'].extend(['artist', entity.artist_type.lower()])
        
        elif isinstance(entity, Recording):
            frontmatter.update({
                'length_ms': entity.length,
                'length_formatted': self._format_duration(entity.length) if entity.length else None,
                'video': entity.video,
                'file_path': entity.file_path,
                'track_number': entity.track_number,
                'disc_number': entity.disc_number,
                'album_id': entity.album_id
            })
            frontmatter['tags'].extend(['recording', 'track'])
        
        elif isinstance(entity, Person):
            frontmatter.update({
                'birth_date': entity.birth_date.isoformat() if entity.birth_date else None,
                'death_date': entity.death_date.isoformat() if entity.death_date else None,
                'gender': entity.gender,
                'country': entity.country,
                'instruments': entity.instruments,
                'roles': entity.roles
            })
            frontmatter['tags'].extend(['person', 'musician'])
            if entity.instruments:
                frontmatter['tags'].extend(entity.instruments)
        
        elif isinstance(entity, Label):
            frontmatter.update({
                'label_code': entity.label_code,
                'country': entity.country,
                'begin_date': entity.begin_date.isoformat() if entity.begin_date else None,
                'end_date': entity.end_date.isoformat() if entity.end_date else None,
                'label_type': entity.label_type
            })
            frontmatter['tags'].extend(['label', 'record_label'])
        
        elif isinstance(entity, Genre):
            frontmatter.update({
                'description': entity.description,
                'parent_genres': entity.parent_genres,
                'child_genres': entity.child_genres
            })
            frontmatter['tags'].extend(['genre', 'style'])
        
        return frontmatter
    
    def _generate_content(self, entity: BaseEntity) -> str:
        """Generate markdown content for entity."""
        content = f"# {entity.name}\n\n"
        
        if entity.metadata and entity.metadata.get('description'):
            content += f"{entity.metadata['description']}\n\n"
        
        if isinstance(entity, Album):
            content += self._generate_album_content(entity)
        elif isinstance(entity, Artist):
            content += self._generate_artist_content(entity)
        elif isinstance(entity, Recording):
            content += self._generate_recording_content(entity)
        elif isinstance(entity, Person):
            content += self._generate_person_content(entity)
        elif isinstance(entity, Label):
            content += self._generate_label_content(entity)
        elif isinstance(entity, Genre):
            content += self._generate_genre_content(entity)
        
        # Add metadata section
        content += "\n## Metadata\n\n"
        content += f"- **Entity Type**: {entity.entity_type.value.title()}\n"
        content += f"- **ID**: `{entity.id}`\n"
        if entity.mbid:
            content += f"- **MusicBrainz ID**: `{entity.mbid}`\n"
        content += f"- **Created**: {entity.created_at.strftime('%Y-%m-%d %H:%M:%S') if entity.created_at else 'Unknown'}\n"
        content += f"- **Updated**: {entity.updated_at.strftime('%Y-%m-%d %H:%M:%S') if entity.updated_at else 'Unknown'}\n"
        
        return content
    
    def _generate_album_content(self, album: Album) -> str:
        """Generate content specific to albums."""
        content = ""
        
        if album.artist_credit:
            content += f"**Artist**: {album.artist_credit}\n\n"
        
        # Album details
        details = []
        if album.release_date:
            details.append(f"**Released**: {album.release_date.strftime('%Y-%m-%d')}")
        if album.label:
            details.append(f"**Label**: {album.label}")
        if album.catalog_number:
            details.append(f"**Catalog**: {album.catalog_number}")
        if album.country:
            details.append(f"**Country**: {album.country}")
        if album.packaging:
            details.append(f"**Format**: {album.packaging}")
        
        if details:
            content += "## Release Information\n\n"
            content += "\n".join([f"- {detail}" for detail in details])
            content += "\n\n"
        
        # Track listing
        if album.total_tracks:
            content += f"## Tracks ({album.total_tracks} tracks"
            if album.total_length:
                content += f", {self._format_duration(album.total_length * 1000)}"
            content += ")\n\n"
            content += "*Track listing to be populated from recordings*\n\n"
        
        # Genres
        if album.genres:
            content += "## Genres\n\n"
            content += ", ".join([f"#{genre}" for genre in album.genres])
            content += "\n\n"
        
        return content
    
    def _generate_artist_content(self, artist: Artist) -> str:
        """Generate content specific to artists."""
        content = ""
        
        if artist.disambiguation:
            content += f"*{artist.disambiguation}*\n\n"
        
        # Artist details
        details = []
        details.append(f"**Type**: {artist.artist_type}")
        if artist.gender:
            details.append(f"**Gender**: {artist.gender}")
        if artist.country:
            details.append(f"**Country**: {artist.country}")
        if artist.begin_date:
            details.append(f"**Active From**: {artist.begin_date.strftime('%Y-%m-%d')}")
        if artist.end_date:
            details.append(f"**Active Until**: {artist.end_date.strftime('%Y-%m-%d')}")
        
        content += "## Artist Information\n\n"
        content += "\n".join([f"- {detail}" for detail in details])
        content += "\n\n"
        
        content += "## Discography\n\n*To be populated from related albums*\n\n"
        content += "## Collaborations\n\n*To be populated from relationships*\n\n"
        
        return content
    
    def _generate_recording_content(self, recording: Recording) -> str:
        """Generate content specific to recordings."""
        content = ""
        
        # Recording details
        details = []
        if recording.length:
            details.append(f"**Duration**: {self._format_duration(recording.length)}")
        if recording.track_number:
            details.append(f"**Track Number**: {recording.track_number}")
        if recording.disc_number:
            details.append(f"**Disc Number**: {recording.disc_number}")
        if recording.video:
            details.append("**Type**: Video")
        if recording.file_path:
            details.append(f"**File**: `{recording.file_path}`")
        
        if details:
            content += "## Recording Information\n\n"
            content += "\n".join([f"- {detail}" for detail in details])
            content += "\n\n"
        
        content += "## Appears On\n\n*To be populated from album relationships*\n\n"
        
        return content
    
    def _generate_person_content(self, person: Person) -> str:
        """Generate content specific to people."""
        content = ""
        
        # Personal details
        details = []
        if person.birth_date:
            details.append(f"**Born**: {person.birth_date.strftime('%Y-%m-%d')}")
        if person.death_date:
            details.append(f"**Died**: {person.death_date.strftime('%Y-%m-%d')}")
        if person.gender:
            details.append(f"**Gender**: {person.gender}")
        if person.country:
            details.append(f"**Country**: {person.country}")
        
        if details:
            content += "## Personal Information\n\n"
            content += "\n".join([f"- {detail}" for detail in details])
            content += "\n\n"
        
        if person.instruments:
            content += "## Instruments\n\n"
            content += ", ".join(person.instruments)
            content += "\n\n"
        
        if person.roles:
            content += "## Roles\n\n"
            content += ", ".join(person.roles)
            content += "\n\n"
        
        content += "## Credits\n\n*To be populated from relationships*\n\n"
        
        return content
    
    def _generate_label_content(self, label: Label) -> str:
        """Generate content specific to labels."""
        content = ""
        
        # Label details
        details = []
        details.append(f"**Type**: {label.label_type}")
        if label.label_code:
            details.append(f"**Label Code**: {label.label_code}")
        if label.country:
            details.append(f"**Country**: {label.country}")
        if label.begin_date:
            details.append(f"**Founded**: {label.begin_date.strftime('%Y-%m-%d')}")
        if label.end_date:
            details.append(f"**Closed**: {label.end_date.strftime('%Y-%m-%d')}")
        
        content += "## Label Information\n\n"
        content += "\n".join([f"- {detail}" for detail in details])
        content += "\n\n"
        
        content += "## Releases\n\n*To be populated from related albums*\n\n"
        
        return content
    
    def _generate_genre_content(self, genre: Genre) -> str:
        """Generate content specific to genres."""
        content = ""
        
        if genre.description:
            content += f"{genre.description}\n\n"
        
        if genre.parent_genres:
            content += "## Parent Genres\n\n"
            content += ", ".join([f"[[{pg}]]" for pg in genre.parent_genres])
            content += "\n\n"
        
        if genre.child_genres:
            content += "## Subgenres\n\n"
            content += ", ".join([f"[[{cg}]]" for cg in genre.child_genres])
            content += "\n\n"
        
        content += "## Artists\n\n*To be populated from related artists*\n\n"
        content += "## Albums\n\n*To be populated from related albums*\n\n"
        
        return content
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize name for use as filename."""
        # Replace problematic characters
        safe_name = name.replace('/', '-').replace('\\', '-').replace(':', '-')
        safe_name = safe_name.replace('?', '').replace('*', '').replace('|', '-')
        safe_name = safe_name.replace('<', '').replace('>', '').replace('"', '')
        return safe_name[:100]  # Limit length
    
    def _format_duration(self, ms: int) -> str:
        """Format duration from milliseconds to MM:SS format."""
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_card_path(self, entity: BaseEntity) -> Path:
        """Get the path where the card would be stored."""
        safe_name = self._sanitize_filename(entity.name)
        filename = f"{safe_name}.md"
        return self.cards_dir / entity.entity_type.value / filename
    
    def card_exists(self, entity: BaseEntity) -> bool:
        """Check if a card already exists for the entity."""
        return self.get_card_path(entity).exists()
    
    def update_card(self, entity: BaseEntity) -> Path:
        """Update existing card or create new one."""
        return self.generate_card(entity)