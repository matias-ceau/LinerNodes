"""
Facade for KnowledgeGraphDB with backend selection.

Activation rules:
- If duckdb is not available OR db_path is ':memory:' -> use in-memory backend
- Else use DuckDB backend

Public import path remains:
from linernodes.knowledge_graph.graph_db import KnowledgeGraphDB
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import (
    Album,
    Artist,
    BaseEntity,
    EntityType,
    Genre,
    Label,
    Person,
    Recording,
    Relationship,
    RelationshipType,
)

logger = logging.getLogger(__name__)


class _InMemoryKnowledgeGraphDB:
    """In-memory backend implementing entity/relationship APIs and release-centric API."""

    def __init__(self, db_path: str | Path | None = None, *args, **kwargs) -> None:
        # Entities/relationships storage (preserve prior behavior)
        self._mem_entities: Dict[str, BaseEntity] = {}
        self._mem_relationships: Dict[str, Relationship] = {}
        self._mem_name_index: Dict[str, str] = {}
        self._mem_rel_index: Dict[str, set[str]] = {}

        # Release API structures
        self._releases: Dict[str, Dict[str, Any]] = {}
        self._insertion_index: Dict[str, int] = {}
        self._counter: int = 1
        self._order_tick: int = 0

    # -------------------------
    # Release API
    # -------------------------
    def add_release(self, release_data: Dict[str, Any]) -> str:
        """Upsert a release and return its id."""
        rid_value = release_data.get("id") or release_data.get("release_id")
        rid: str
        if rid_value:
            rid = str(rid_value)
        else:
            title = str(release_data.get("title") or "").strip()
            artist = str(release_data.get("artist") or "").strip()
            if title or artist:
                basis = f"{title.lower()}::{artist.lower()}".encode("utf-8")
                rid = hashlib.sha1(basis).hexdigest()[:12]
            else:
                rid = f"mem-{self._counter:06d}"
                self._counter += 1

        existing = self._releases.get(rid, {})
        merged = {**existing, **release_data}
        merged["id"] = rid
        self._releases[rid] = merged

        if rid not in self._insertion_index:
            self._insertion_index[rid] = self._order_tick
            self._order_tick += 1

        return rid

    def get_stats(self) -> Dict[str, int]:
        """Return basic counts for the release store."""
        return {"releases": len(self._releases)}

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search releases by title or artist using simple scoring."""
        if not query or not str(query).strip():
            return []
        q = str(query).lower()

        def tokens(s: str) -> set[str]:
            # split on whitespace and simple punctuation
            import re

            return set(filter(None, re.split(r"[\s\W_]+", s.lower())))

        results: List[tuple[int, int, str, Dict[str, Any]]] = []
        for rid, r in self._releases.items():
            title_l = str(r.get("title", "")).lower()
            artist_l = str(r.get("artist", "")).lower()
            score = 0
            if q in tokens(title_l) or q in tokens(artist_l):
                score = 2
            elif q in title_l or q in artist_l:
                score = 1
            if score > 0:
                results.append(
                    (
                        score,
                        self._insertion_index.get(rid, 1_000_000_000),
                        rid,
                        r,
                    )
                )

        results.sort(key=lambda t: (-t[0], t[1], t[2]))
        out: List[Dict[str, Any]] = []
        for _, _, rid, r in results[: max(0, int(limit))]:
            shallow = dict(r)
            shallow["id"] = rid
            out.append(shallow)
        return out

    def show(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Return a shallow copy of the release data if present."""
        if identifier in self._releases:
            d = dict(self._releases[identifier])
            d["id"] = identifier
            return d
        return None

    def close(self) -> None:
        """No-op for the in-memory backend."""
        return None

    # -------------------------
    # Entity/Relationship API (preserve previous in-memory behavior)
    # -------------------------
    def create_schema(self) -> None:
        """No-op for in-memory backend."""
        return None

    def add_entity(self, entity: BaseEntity) -> bool:
        """Add or replace an entity in memory."""
        try:
            self._mem_entities[entity.id] = entity
            self._mem_name_index[entity.id] = (entity.name or "").lower()
            return True
        except Exception as e:  # pragma: no cover - defensive
            print(f"Error adding entity {entity.id}: {e}")
            return False

    def get_entity(self, entity_id: str) -> Optional[BaseEntity]:
        """Get entity by id."""
        return self._mem_entities.get(entity_id)

    def get_albums(self) -> List[Album]:
        """Return all Album entities."""
        return [e for e in self._mem_entities.values() if isinstance(e, Album)]

    def search_entities(
        self, query: str, entity_type: Optional[EntityType] = None
    ) -> List[BaseEntity]:
        """Simple name contains search on entities."""
        q = (query or "").lower()
        out: List[BaseEntity] = []
        for e in self._mem_entities.values():
            if q in (e.name or "").lower():
                if entity_type is None or e.entity_type == entity_type:
                    out.append(e)
        return out

    def add_relationship(self, relationship: Relationship) -> bool:
        """Add a relationship between entities."""
        try:
            rel_id = (
                relationship.id
                or f"{relationship.source_id}->{relationship.relationship_type.value}->{relationship.target_id}"
            )
            new_rel = Relationship(
                id=rel_id,
                source_id=relationship.source_id,
                target_id=relationship.target_id,
                relationship_type=relationship.relationship_type,
                attributes=relationship.attributes or {},
                begin_date=relationship.begin_date,
                end_date=relationship.end_date,
                created_at=relationship.created_at,
            )
            self._mem_relationships[rel_id] = new_rel
            self._mem_rel_index.setdefault(relationship.source_id, set()).add(rel_id)
            self._mem_rel_index.setdefault(relationship.target_id, set()).add(rel_id)
            return True
        except Exception as e:  # pragma: no cover - defensive
            print(f"Error adding relationship: {e}")
            return False

    def get_relationships(self, entity_id: str) -> List[Relationship]:
        """Return all relationships connected to an entity."""
        rels: List[Relationship] = []
        try:
            for rel in self._mem_relationships.values():
                if rel.source_id == entity_id or rel.target_id == entity_id:
                    rels.append(rel)
        except Exception as e:  # pragma: no cover - defensive
            print(f"Error retrieving relationships: {e}")
        return rels

    def get_connected_entities(
        self, entity_id: str, relationship_type: Optional[RelationshipType] = None
    ) -> List[BaseEntity]:
        """Return entities connected to entity_id, optionally filtered by type."""
        out: List[BaseEntity] = []
        seen: set[str] = set()
        for rel in self.get_relationships(entity_id):
            if relationship_type and rel.relationship_type != relationship_type:
                continue
            other = rel.target_id if rel.source_id == entity_id else rel.source_id
            if other == entity_id or other in seen:
                continue
            seen.add(other)
            ent = self._mem_entities.get(other)
            if ent:
                out.append(ent)
        return out


class _DuckDBKnowledgeGraphDB:
    """DuckDB-backed implementation preserving previous on-disk behavior."""

    def __init__(self, db_path: str | Path | None = None, *args, **kwargs) -> None:
        import duckdb  # local import by design

        self.db_path = str(db_path or ":memory:")
        self.conn = duckdb.connect(self.db_path)
        self.create_schema()

    def close(self) -> None:
        """Close the DuckDB connection if open."""
        try:
            self.conn.close()
        except Exception:  # pragma: no cover - defensive
            pass

    # -------------------------
    # Release API (stubbed)
    # -------------------------
    def add_release(self, release_data: Dict[str, Any]) -> str:  # pragma: no cover
        """Not implemented for DuckDB backend yet."""
        raise NotImplementedError("add_release not implemented on DuckDB backend")

    def get_stats(self) -> Dict[str, int]:  # pragma: no cover
        """Not implemented for DuckDB backend yet."""
        raise NotImplementedError("get_stats not implemented on DuckDB backend")

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:  # pragma: no cover
        """Not implemented for DuckDB backend yet."""
        raise NotImplementedError("search not implemented on DuckDB backend")

    def show(self, identifier: str) -> Optional[Dict[str, Any]]:  # pragma: no cover
        """Not implemented for DuckDB backend yet."""
        raise NotImplementedError("show not implemented on DuckDB backend")

    # -------------------------
    # Entity/Relationship API (migrated from previous implementation)
    # -------------------------
    def create_schema(self) -> None:
        """Create the database schema for knowledge graph storage."""
        self.conn.execute(
            """
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
            """
        )

        self.conn.execute(
            """
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
            """
        )

        # Indexes
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_mbid ON entities(mbid)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relationship_type)")

    def add_entity(self, entity: BaseEntity) -> bool:
        """Add an entity to DuckDB store."""
        try:
            base_data: Dict[str, Any] = {
                "id": entity.id,
                "entity_type": entity.entity_type.value,
                "name": entity.name,
                "mbid": entity.mbid,
                "created_at": entity.created_at,
                "updated_at": entity.updated_at,
                "metadata": json.dumps(entity.metadata) if entity.metadata else None,
            }

            if isinstance(entity, Album):
                base_data.update(
                    {
                        "artist_credit": entity.artist_credit,
                        "release_date": entity.release_date,
                        "label": entity.label,
                        "catalog_number": entity.catalog_number,
                        "barcode": entity.barcode,
                        "country": entity.country,
                        "status": entity.status,
                        "packaging": entity.packaging,
                        "total_tracks": entity.total_tracks,
                        "total_length": entity.total_length,
                        "genres": json.dumps(entity.genres),
                        "recordings": json.dumps(entity.recordings),
                    }
                )
            elif isinstance(entity, Artist):
                base_data.update(
                    {
                        "sort_name": entity.sort_name,
                        "disambiguation": entity.disambiguation,
                        "artist_type": entity.artist_type,
                        "gender": entity.gender,
                        "country": entity.country,
                        "begin_date": entity.begin_date,
                        "end_date": entity.end_date,
                        "ended": entity.ended,
                    }
                )
            elif isinstance(entity, Recording):
                base_data.update(
                    {
                        "length": entity.length,
                        "disambiguation": entity.disambiguation,
                        "video": entity.video,
                        "file_path": entity.file_path,
                        "track_number": entity.track_number,
                        "disc_number": entity.disc_number,
                        "album_id": entity.album_id,
                    }
                )
            elif isinstance(entity, Person):
                base_data.update(
                    {
                        "birth_date": entity.birth_date,
                        "death_date": entity.death_date,
                        "gender": entity.gender,
                        "country": entity.country,
                        "instruments": json.dumps(entity.instruments),
                        "roles": json.dumps(entity.roles),
                    }
                )
            elif isinstance(entity, Label):
                base_data.update(
                    {
                        "label_code": entity.label_code,
                        "country": entity.country,
                        "begin_date": entity.begin_date,
                        "end_date": entity.end_date,
                        "label_type": entity.label_type,
                    }
                )
            elif isinstance(entity, Genre):
                base_data.update(
                    {
                        "description": entity.description,
                        "parent_genres": json.dumps(entity.parent_genres),
                        "child_genres": json.dumps(entity.child_genres),
                    }
                )

            columns = list(base_data.keys())
            placeholders = ", ".join(["?" for _ in columns])
            values = list(base_data.values())

            query = f"""
                INSERT OR REPLACE INTO entities ({', '.join(columns)})
                VALUES ({placeholders})
            """
            self.conn.execute(query, values)
            return True
        except Exception as e:  # pragma: no cover - defensive
            print(f"Error adding entity {entity.id}: {e}")
            return False

    def get_entity(self, entity_id: str) -> Optional[BaseEntity]:
        """Retrieve an entity by ID from DuckDB store."""
        try:
            result = self.conn.execute("SELECT * FROM entities WHERE id = ?", (entity_id,)).fetchone()
            if not result:
                return None
            return self._row_to_entity(result)
        except Exception as e:  # pragma: no cover - defensive
            print(f"Error retrieving entity {entity_id}: {e}")
            return None

    def get_albums(self) -> List[Album]:
        """Return all albums from DuckDB store."""
        try:
            results = self.conn.execute(
                "SELECT * FROM entities WHERE entity_type = ?", (EntityType.ALBUM.value,)
            ).fetchall()
            return [self._row_to_entity(row) for row in results if row]  # type: ignore[list-item]
        except Exception as e:  # pragma: no cover - defensive
            print(f"Error retrieving albums: {e}")
            return []

    def search_entities(self, query: str, entity_type: Optional[EntityType] = None) -> List[BaseEntity]:
        """Search entities by name with optional type filter."""
        try:
            sql = "SELECT * FROM entities WHERE name ILIKE ?"
            params: List[Any] = [f"%{query}%"]
            if entity_type:
                sql += " AND entity_type = ?"
                params.append(entity_type.value)
            results = self.conn.execute(sql, params).fetchall()
            return [self._row_to_entity(row) for row in results if row]  # type: ignore[list-item]
        except Exception as e:  # pragma: no cover - defensive
            print(f"Error searching entities: {e}")
            return []

    def add_relationship(self, relationship: Relationship) -> bool:
        """Add a relationship into DuckDB store."""
        try:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO relationships
                (id, source_id, target_id, relationship_type, attributes, begin_date, end_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    relationship.id,
                    relationship.source_id,
                    relationship.target_id,
                    relationship.relationship_type.value,
                    json.dumps(relationship.attributes) if relationship.attributes else None,
                    relationship.begin_date,
                    relationship.end_date,
                    relationship.created_at,
                ),
            )
            return True
        except Exception as e:  # pragma: no cover - defensive
            print(f"Error adding relationship: {e}")
            return False

    def get_relationships(self, entity_id: str) -> List[Relationship]:
        """Return relationships for an entity from DuckDB store."""
        try:
            results = self.conn.execute(
                """
                SELECT * FROM relationships
                WHERE source_id = ? OR target_id = ?
                """,
                (entity_id, entity_id),
            ).fetchall()

            relationships: List[Relationship] = []
            for row in results:
                rel = Relationship(
                    id=row[0],
                    source_id=row[1],
                    target_id=row[2],
                    relationship_type=RelationshipType(row[3]),
                    attributes=json.loads(row[4]) if row[4] else {},
                    begin_date=row[5],
                    end_date=row[6],
                    created_at=row[7],
                )
                relationships.append(rel)
            return relationships
        except Exception as e:  # pragma: no cover - defensive
            print(f"Error retrieving relationships: {e}")
            return []

    def get_connected_entities(
        self, entity_id: str, relationship_type: Optional[RelationshipType] = None
    ) -> List[BaseEntity]:
        """Return entities connected to the given entity from DuckDB store."""
        try:
            sql = """
                SELECT e.* FROM entities e
                JOIN relationships r ON (e.id = r.source_id OR e.id = r.target_id)
                WHERE (r.source_id = ? OR r.target_id = ?) AND e.id != ?
            """
            params: List[Any] = [entity_id, entity_id, entity_id]
            if relationship_type:
                sql += " AND r.relationship_type = ?"
                params.append(relationship_type.value)
            results = self.conn.execute(sql, params).fetchall()
            return [self._row_to_entity(row) for row in results if row]  # type: ignore[list-item]
        except Exception as e:  # pragma: no cover - defensive
            print(f"Error retrieving connected entities: {e}")
            return []

    def _row_to_entity(self, row) -> Optional[BaseEntity]:
        """Convert a DuckDB row to a proper entity instance."""
        if not row:
            return None
        try:
            entity_type = EntityType(row[1])
            common_fields = {
                "id": row[0],
                "name": row[2],
                "mbid": row[3],
                "created_at": row[4],
                "updated_at": row[5],
                "metadata": json.loads(row[6]) if row[6] else {},
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
                    **common_fields,
                )
            elif entity_type == EntityType.ARTIST:
                return Artist(
                    entity_type=entity_type,
                    sort_name=row[19] or common_fields["name"],
                    disambiguation=row[20] or "",
                    artist_type=row[21] or "Person",
                    gender=row[22],
                    country=row[12],
                    begin_date=row[23],
                    end_date=row[24],
                    ended=row[25] or False,
                    **common_fields,
                )
            # Fallback to base entity for other types
            return BaseEntity(entity_type=entity_type, **common_fields)
        except Exception as e:  # pragma: no cover - defensive
            print(f"Error converting row to entity: {e}")
            return None


class KnowledgeGraphDB:
    """Facade selecting backend at construction time."""

    def __new__(cls, db_path: str | Path | None = None, *args, **kwargs):  # type: ignore[override]
        """Select appropriate backend.

        - If duckdb import fails OR db_path == ':memory:' -> in-memory backend
        - Else -> DuckDB backend
        """
        path_str = str(db_path or ":memory:")
        duckdb_available = False
        try:
            import duckdb as _duckdb_available_marker  # type: ignore  # noqa: F401
            duckdb_available = True
        except Exception:  # pragma: no cover - defensive
            duckdb_available = False

        use_memory = (not duckdb_available) or (path_str == ":memory:")
        if use_memory:
            logger.debug("KnowledgeGraphDB selecting in-memory backend for path %s", path_str)
            instance = _InMemoryKnowledgeGraphDB(db_path, *args, **kwargs)
        else:
            logger.debug("KnowledgeGraphDB selecting DuckDB backend for path %s", path_str)
            instance = _DuckDBKnowledgeGraphDB(db_path, *args, **kwargs)

        return instance

    # Keep consistent signature; init never runs because __new__ returns backend
    def __init__(self, db_path: str | Path | None = None, *args, **kwargs) -> None:  # pragma: no cover - facade
        pass