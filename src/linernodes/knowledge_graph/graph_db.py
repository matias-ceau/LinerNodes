import duckdb
import json
from typing import List, Optional, Dict, Any, Set, Tuple
from pathlib import Path
from datetime import datetime

from .models import (
    BaseEntity, Album, Artist, Genre, Recording, Person, Label,
    Relationship, EntityType, RelationshipType
)

class KnowledgeGraphDB:
    """DuckDB-based knowledge graph storage for music entities and relationships."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the knowledge graph database."""
        self.db_path = db_path or ":memory:"
        self.conn = duckdb.connect(self.db_path)
        self.create_schema()
    
    def create_schema(self):
        """Create the database schema for knowledge graph storage."""
        
        # Entities table - stores all entity types
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id VARCHAR PRIMARY KEY,
                entity_type VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                mbid VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSON,
                -- Album-specific fields
                artist_credit VARCHAR,
                release_date DATE,
                label VARCHAR,
                catalog_number VARCHAR,
                barcode VARCHAR,
                country VARCHAR,
                status VARCHAR,
                packaging VARCHAR,
                total_tracks INTEGER,
                total_length INTEGER,
                genres JSON,
                recordings JSON,
                -- Artist-specific fields
                sort_name VARCHAR,
                disambiguation VARCHAR,
                artist_type VARCHAR,
                gender VARCHAR,
                begin_date DATE,
                end_date DATE,
                ended BOOLEAN,
                -- Recording-specific fields
                length INTEGER,
                video BOOLEAN,
                file_path VARCHAR,
                track_number INTEGER,
                disc_number INTEGER,
                album_id VARCHAR,
                -- Person-specific fields
                birth_date DATE,
                death_date DATE,
                instruments JSON,
                roles JSON,
                -- Label-specific fields
                label_code VARCHAR,
                label_type VARCHAR,
                -- Genre-specific fields
                description TEXT,
                parent_genres JSON,
                child_genres JSON
            )
        """)
        
        # Relationships table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id VARCHAR PRIMARY KEY,
                source_id VARCHAR NOT NULL,
                target_id VARCHAR NOT NULL,
                relationship_type VARCHAR NOT NULL,
                attributes JSON,
                begin_date DATE,
                end_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES entities(id),
                FOREIGN KEY (target_id) REFERENCES entities(id)
            )
        """)
        
        # Create indexes for performance
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_mbid ON entities(mbid)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relationship_type)")
    
    def add_entity(self, entity: BaseEntity) -> bool:
        """Add an entity to the knowledge graph."""
        try:
            # Prepare entity data based on type
            base_data = {
                'id': entity.id,
                'entity_type': entity.entity_type.value,
                'name': entity.name,
                'mbid': entity.mbid,
                'created_at': entity.created_at,
                'updated_at': entity.updated_at,
                'metadata': json.dumps(entity.metadata) if entity.metadata else None
            }
            
            # Add type-specific fields
            if isinstance(entity, Album):
                base_data.update({
                    'artist_credit': entity.artist_credit,
                    'release_date': entity.release_date,
                    'label': entity.label,
                    'catalog_number': entity.catalog_number,
                    'barcode': entity.barcode,
                    'country': entity.country,
                    'status': entity.status,
                    'packaging': entity.packaging,
                    'total_tracks': entity.total_tracks,
                    'total_length': entity.total_length,
                    'genres': json.dumps(entity.genres),
                    'recordings': json.dumps(entity.recordings)
                })
            
            elif isinstance(entity, Artist):
                base_data.update({
                    'sort_name': entity.sort_name,
                    'disambiguation': entity.disambiguation,
                    'artist_type': entity.artist_type,
                    'gender': entity.gender,
                    'country': entity.country,
                    'begin_date': entity.begin_date,
                    'end_date': entity.end_date,
                    'ended': entity.ended
                })
            
            elif isinstance(entity, Recording):
                base_data.update({
                    'length': entity.length,
                    'disambiguation': entity.disambiguation,
                    'video': entity.video,
                    'file_path': entity.file_path,
                    'track_number': entity.track_number,
                    'disc_number': entity.disc_number,
                    'album_id': entity.album_id
                })
            
            elif isinstance(entity, Person):
                base_data.update({
                    'birth_date': entity.birth_date,
                    'death_date': entity.death_date,
                    'gender': entity.gender,
                    'country': entity.country,
                    'instruments': json.dumps(entity.instruments),
                    'roles': json.dumps(entity.roles)
                })
            
            elif isinstance(entity, Label):
                base_data.update({
                    'label_code': entity.label_code,
                    'country': entity.country,
                    'begin_date': entity.begin_date,
                    'end_date': entity.end_date,
                    'label_type': entity.label_type
                })
            
            elif isinstance(entity, Genre):
                base_data.update({
                    'description': entity.description,
                    'parent_genres': json.dumps(entity.parent_genres),
                    'child_genres': json.dumps(entity.child_genres)
                })
            
            # Build INSERT query
            columns = list(base_data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            values = list(base_data.values())
            
            query = f"""
                INSERT OR REPLACE INTO entities ({', '.join(columns)})
                VALUES ({placeholders})
            """
            
            self.conn.execute(query, values)
            return True
            
        except Exception as e:
            print(f"Error adding entity {entity.id}: {e}")
            return False
    
    def get_entity(self, entity_id: str) -> Optional[BaseEntity]:
        """Retrieve an entity by ID."""
        try:
            result = self.conn.execute(
                "SELECT * FROM entities WHERE id = ?", 
                (entity_id,)
            ).fetchone()
            
            if not result:
                return None
                
            return self._row_to_entity(result)
            
        except Exception as e:
            print(f"Error retrieving entity {entity_id}: {e}")
            return None
    
    def get_albums(self) -> List[Album]:
        """Get all albums in the knowledge graph."""
        try:
            results = self.conn.execute(
                "SELECT * FROM entities WHERE entity_type = ?",
                (EntityType.ALBUM.value,)
            ).fetchall()
            
            return [self._row_to_entity(row) for row in results if row]
            
        except Exception as e:
            print(f"Error retrieving albums: {e}")
            return []
    
    def search_entities(self, query: str, entity_type: Optional[EntityType] = None) -> List[BaseEntity]:
        """Search entities by name."""
        try:
            sql = "SELECT * FROM entities WHERE name ILIKE ?"
            params = [f"%{query}%"]
            
            if entity_type:
                sql += " AND entity_type = ?"
                params.append(entity_type.value)
                
            results = self.conn.execute(sql, params).fetchall()
            return [self._row_to_entity(row) for row in results if row]
            
        except Exception as e:
            print(f"Error searching entities: {e}")
            return []
    
    def add_relationship(self, relationship: Relationship) -> bool:
        """Add a relationship between entities."""
        try:
            self.conn.execute("""
                INSERT OR REPLACE INTO relationships 
                (id, source_id, target_id, relationship_type, attributes, begin_date, end_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                relationship.id,
                relationship.source_id,
                relationship.target_id,
                relationship.relationship_type.value,
                json.dumps(relationship.attributes) if relationship.attributes else None,
                relationship.begin_date,
                relationship.end_date,
                relationship.created_at
            ))
            return True
            
        except Exception as e:
            print(f"Error adding relationship: {e}")
            return False
    
    def get_relationships(self, entity_id: str) -> List[Relationship]:
        """Get all relationships for an entity."""
        try:
            results = self.conn.execute("""
                SELECT * FROM relationships 
                WHERE source_id = ? OR target_id = ?
            """, (entity_id, entity_id)).fetchall()
            
            relationships = []
            for row in results:
                rel = Relationship(
                    id=row[0],
                    source_id=row[1],
                    target_id=row[2],
                    relationship_type=RelationshipType(row[3]),
                    attributes=json.loads(row[4]) if row[4] else {},
                    begin_date=row[5],
                    end_date=row[6],
                    created_at=row[7]
                )
                relationships.append(rel)
                
            return relationships
            
        except Exception as e:
            print(f"Error retrieving relationships: {e}")
            return []
    
    def get_connected_entities(self, entity_id: str, relationship_type: Optional[RelationshipType] = None) -> List[BaseEntity]:
        """Get entities connected to the given entity."""
        try:
            sql = """
                SELECT e.* FROM entities e
                JOIN relationships r ON (e.id = r.source_id OR e.id = r.target_id)
                WHERE (r.source_id = ? OR r.target_id = ?) AND e.id != ?
            """
            params = [entity_id, entity_id, entity_id]
            
            if relationship_type:
                sql += " AND r.relationship_type = ?"
                params.append(relationship_type.value)
            
            results = self.conn.execute(sql, params).fetchall()
            return [self._row_to_entity(row) for row in results if row]
            
        except Exception as e:
            print(f"Error retrieving connected entities: {e}")
            return []
    
    def _row_to_entity(self, row) -> Optional[BaseEntity]:
        """Convert database row to appropriate entity type."""
        if not row:
            return None
            
        try:
            entity_type = EntityType(row[1])  # entity_type column
            
            common_fields = {
                'id': row[0],
                'name': row[2],
                'mbid': row[3],
                'created_at': row[4],
                'updated_at': row[5],
                'metadata': json.loads(row[6]) if row[6] else {}
            }
            
            if entity_type == EntityType.ALBUM:
                return Album(
                    entity_type=entity_type,
                    artist_credit=row[7] or "",
                    release_date=row[8],
                    label=row[9],
                    catalog_number=row[10],
                    barcode=row[11],
                    country=row[12],
                    status=row[13] or "Official",
                    packaging=row[14],
                    total_tracks=row[15] or 0,
                    total_length=row[16],
                    genres=json.loads(row[17]) if row[17] else [],
                    recordings=json.loads(row[18]) if row[18] else [],
                    **common_fields
                )
            
            elif entity_type == EntityType.ARTIST:
                return Artist(
                    entity_type=entity_type,
                    sort_name=row[19] or common_fields['name'],
                    disambiguation=row[20] or "",
                    artist_type=row[21] or "Person",
                    gender=row[22],
                    country=row[12],
                    begin_date=row[23],
                    end_date=row[24],
                    ended=row[25] or False,
                    **common_fields
                )
            
            # Add other entity types as needed...
            # For now, return base entity
            return BaseEntity(entity_type=entity_type, **common_fields)
            
        except Exception as e:
            print(f"Error converting row to entity: {e}")
            return None