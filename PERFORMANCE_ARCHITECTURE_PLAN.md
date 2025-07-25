# LinerNodes Performance Architecture Redesign

## 🛣️ Old Roadmap

### Phase 1: Core Foundation ✅
- [x] MPD integration and local file support
- [x] Basic CLI and configuration system
- [x] SQLite database architecture
- [x] MusicBrainz integration

### Phase 2: Multi-Source Integration 🔄
- [ ] Streaming API integrations (Spotify, Apple Music)
- [ ] Cloud storage connectors (Google Drive, Dropbox)
- [ ] S3 and object storage support
- [ ] Smart deduplication across sources

### Phase 3: Advanced Features 📋
- [ ] Machine learning for music recommendation
- [ ] Advanced graph analytics and visualization
- [ ] Custom metadata schemas
- [ ] Plugin system for extensibility

### Phase 4: Scale & Performance 📋
- [ ] Optional PostgreSQL backend for large collections
- [ ] Distributed processing for massive libraries
- [ ] Real-time synchronization across sources
- [ ] Advanced caching and indexing


## 🚨 Current Problems Identified

### Performance Bottlenecks
- **68.3% CPU usage** on graph interface 
- **N+1 Query Problem**: Individual `get_album_tracks()` calls for 1,395 albums
- **Inefficient NetworkX Usage**: Building 9K+ node graph with redundant metadata
- **SQLite Limitations**: Not optimized for graph traversal patterns
- **Memory Overhead**: Storing full metadata in graph nodes

### Architecture Issues
- Single SQLite database handling both metadata storage AND graph operations
- No separation between transactional data and analytical/graph queries
- Graph regeneration on every request despite caching attempts
- Complex relationship queries forcing expensive JOINs

## 🎯 Proposed Multi-Database Architecture

### Phase 1: Immediate Performance Fixes (Day 1)
**Goal**: Reduce CPU from 68% to <10% for current dataset

1. **Fix N+1 Query Problem**
   - Replace individual `get_album_tracks()` with single bulk query
   - Use `get_all_tracks_with_albums()` instead of nested loops
   - Implement batch loading with proper JOINs

2. **Optimize NetworkX Graph Building**  
   - Pre-allocate nodes and edges lists
   - Use `graph.add_nodes_from()` and `graph.add_edges_from()` for bulk operations
   - Store minimal data in nodes (just IDs), fetch details on demand

3. **Implement Smart Caching**
   - Cache at database query level, not graph object level
   - Use file-based cache for relationship data
   - Invalidate cache only when database changes

### Phase 2: Hybrid Database Architecture (Week 1)
**Goal**: Support 50K+ nodes with sub-second response times

#### Database Layer Separation
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   SQLite DB     │    │  In-Memory Graph │    │  Graph Cache    │
│                 │    │                  │    │                 │
│ • Metadata      │◄──►│ • NetworkX       │◄──►│ • Pickle/JSON   │
│ • Sources       │    │ • Relationships  │    │ • Fast Load     │
│ • Playlists     │    │ • Traversal      │    │ • Incremental   │
│ • History       │    │ • Analytics      │    │ • Persistence   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

#### Core Components

1. **SQLite Database** (Authoritative Source)
   - Purpose: Metadata storage, source management, user data
   - Schema: Current schema remains unchanged
   - Optimizations: Add graph-specific indexes

2. **In-Memory Graph Database** (Performance Layer)  
   - Purpose: Fast graph operations, traversal, visualization
   - Technology: NetworkX + custom optimizations OR MemGraph
   - Features:
     - Relationship-first storage
     - Fast neighbor queries  
     - Efficient subgraph extraction
     - Memory-mapped for persistence

3. **Graph Synchronization Service**
   - Purpose: Keep graph DB in sync with SQLite changes
   - Triggers: On SQLite INSERT/UPDATE/DELETE
   - Operations: Incremental graph updates
   - Conflict resolution: SQLite is authoritative

### Phase 3: Advanced Graph Solutions (Week 2)
**Goal**: Research and potentially implement dedicated graph database

#### Option A: Enhanced NetworkX
**Pros**: 
- Already integrated
- Pure Python
- Good for current scale (10K nodes)
- No additional dependencies

**Optimizations**:
- Custom node/edge data structures
- Memory-mapped backing store
- Lazy loading of node attributes
- Efficient serialization (pickle/msgpack)

#### Option B: MemGraph Integration
**Pros**:
- Purpose-built for graph operations
- Cypher query language
- Excellent performance (1M+ nodes)
- In-memory with persistence

**Implementation**:
```python
# Graph queries in Cypher instead of complex SQL JOINs
MATCH (artist:Artist)-[:RECORDED]->(album:Album)-[:CONTAINS]->(track:Track)
WHERE artist.name CONTAINS "Ron Carter"
RETURN artist, album, track
```

**Cons**:
- Additional dependency
- Learning curve
- May be overkill for current scale

#### Option C: Custom Graph Store
**Pros**:
- Tailored for music domain
- Minimal memory footprint
- Direct integration

**Implementation**:
```python
class MusicGraphStore:
    def __init__(self):
        self.nodes = {}  # id -> {type, name, metadata}
        self.edges = defaultdict(set)  # node_id -> set(connected_ids)
        self.reverse_edges = defaultdict(set)  # for bidirectional
        self.indexes = {
            'by_type': defaultdict(set),
            'by_name': {},  # name -> node_id
            'by_artist': defaultdict(set)  # artist -> album_ids
        }
```

### Phase 4: Performance Monitoring & Scaling (Week 3)

#### Benchmarking Framework
- Performance tests for different node counts (1K, 10K, 50K, 100K)
- Memory usage profiling
- Query response time monitoring
- CPU utilization tracking

#### Auto-scaling Strategies
- Adaptive algorithms based on dataset size
- Progressive loading for very large graphs
- Streaming graph updates
- Background precomputation

## 🚀 Implementation Priority

### Immediate (This Session)
1. ✅ Fix N+1 query problem  
2. ✅ Optimize NetworkX bulk operations
3. ✅ Implement query result caching
4. ✅ Test performance improvement

### Short Term (Next Few Days)
1. Design graph synchronization service
2. Implement incremental graph updates  
3. Add proper graph persistence
4. Create performance benchmarks

### Medium Term (Next Week)
1. Research MemGraph integration feasibility
2. Prototype custom graph store
3. Implement hybrid architecture
4. Performance comparison testing

### Long Term (Future Enhancements)
1. WebGL-based visualization for 100K+ nodes
2. Distributed graph processing
3. Real-time graph updates
4. Advanced graph analytics (centrality, communities, etc.)

## 🔧 Technical Implementation Details

### Database Schema Optimizations
```sql
-- Add graph-specific indexes
CREATE INDEX idx_tracks_album_id ON tracks(album_id);
CREATE INDEX idx_albums_artist ON albums(artist_credit);
CREATE INDEX idx_track_metadata ON tracks(title, artist_credit);

-- Materialized view for graph relationships
CREATE VIEW graph_relationships AS
SELECT 
    'album' as source_type, albums.id as source_id, albums.title as source_name,
    'artist' as target_type, albums.artist_credit as target_id, albums.artist_credit as target_name,
    'performed_by' as relationship_type
FROM albums WHERE albums.artist_credit IS NOT NULL
UNION ALL
SELECT 
    'track' as source_type, tracks.id as source_id, tracks.title as source_name,
    'album' as target_type, tracks.album_id as target_id, albums.title as target_name,
    'belongs_to' as relationship_type  
FROM tracks JOIN albums ON tracks.album_id = albums.id;
```

### Graph Loading Strategy
```python
def load_graph_efficiently():
    # Single query to get all relationships
    relationships = db.execute("""
        SELECT source_type, source_id, source_name, 
               target_type, target_id, target_name, 
               relationship_type
        FROM graph_relationships 
        LIMIT ?
    """, (max_nodes,))
    
    # Bulk create nodes and edges
    nodes = []
    edges = []
    
    for rel in relationships:
        nodes.extend([
            (f"{rel.source_type}_{rel.source_id}", {
                'name': rel.source_name, 
                'type': rel.source_type
            }),
            (f"{rel.target_type}_{rel.target_id}", {
                'name': rel.target_name,
                'type': rel.target_type  
            })
        ])
        edges.append((f"{rel.source_type}_{rel.source_id}", 
                      f"{rel.target_type}_{rel.target_id}"))
    
    # Bulk operations
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)
```

## 📊 Success Metrics

### Performance Targets
- **10K nodes**: <2 seconds loading, <5% CPU
- **50K nodes**: <10 seconds loading, <15% CPU  
- **100K nodes**: <30 seconds loading, <25% CPU

### Memory Targets
- **10K nodes**: <100MB total memory
- **50K nodes**: <500MB total memory
- **100K nodes**: <1GB total memory

### User Experience Targets
- Graph interaction: <100ms response time
- Search results: <500ms response time
- Graph updates: <1 second propagation time

This architecture ensures LinerNodes can truly handle the "oceanic boundlessness" of musical data without artificial limits or performance degradation.
