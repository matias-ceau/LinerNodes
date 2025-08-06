"""
Fast Graph Explorer - Local Data Only
No external API calls, optimized for beets/local databases
"""

import streamlit as st
import plotly.graph_objects as go
import networkx as nx
from typing import Dict, Optional
import sys
from pathlib import Path
import time

# Handle imports
try:
    from ..backend.database.models import DatabaseManager, Track, Album, Artist
    from ..backend.database.database import LinerDatabase
except ImportError:
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from linernodes.backend.database.models import DatabaseManager


class FastMusicGraphExplorer:
    """Ultra-fast graph explorer using local data only."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize with local database only."""
        self.db_manager = DatabaseManager(Path(db_path) if db_path else None)
        
        # Color scheme
        self.entity_colors = {
            'album': '#ff6b6b',
            'artist': '#4ecdc4', 
            'track': '#45b7d1',
            'genre': '#96ceb4',
        }
        
        # Performance cache
        self._cache = {}
        
    @st.cache_data
    def get_graph_data(_self, max_nodes: int = 5000) -> Dict:
        """Get graph data using single optimized query - NO external calls."""
        start_time = time.time()
        
        # Single query to get all relationships efficiently
        with _self.db_manager.db.connection() as conn:
            # Get albums with track counts (no external API calls)
            albums_query = """
            SELECT a.id, a.title, a.artist_credit, COUNT(t.id) as track_count
            FROM albums a
            LEFT JOIN tracks t ON a.id = t.album_id  
            GROUP BY a.id, a.title, a.artist_credit
            ORDER BY track_count DESC
            LIMIT ?
            """
            
            albums = conn.execute(albums_query, (min(max_nodes // 3, 1000),)).fetchall()
            
            # Get tracks for selected albums (batch query, no API calls)
            album_ids = [str(a['id']) for a in albums]
            if not album_ids:
                return {'nodes': [], 'edges': [], 'stats': {'node_count': 0, 'edge_count': 0}}
                
            tracks_query = f"""
            SELECT t.id, t.title, t.album_id, t.artist_credit, t.genre, t.length
            FROM tracks t
            WHERE t.album_id IN ({','.join(['?'] * len(album_ids))})
            ORDER BY t.album_id, t.track
            LIMIT ?
            """
            
            tracks = conn.execute(tracks_query, album_ids + [max_nodes]).fetchall()
        
        # Build graph data structures efficiently
        nodes = []
        edges = []
        node_set = set()
        
        # Artist aggregation (no duplicates)
        artists = {}
        
        # Process albums (fast local data only)
        for album in albums:
            album_id = f"album_{album['id']}"
            if album_id not in node_set:
                nodes.append({
                    'id': album_id,
                    'name': album['title'][:50],  # Truncate for performance
                    'type': 'album',
                    'size': min(25 + album['track_count'] * 2, 50),
                    'color': _self.entity_colors['album']
                })
                node_set.add(album_id)
            
            # Artist connection (local only)
            if album['artist_credit']:
                artist_id = f"artist_{album['artist_credit']}"
                if artist_id not in artists:
                    artists[artist_id] = {
                        'name': album['artist_credit'][:40],
                        'albums': []
                    }
                artists[artist_id]['albums'].append(album_id)
        
        # Add artist nodes (aggregated, no API calls)
        for artist_id, artist_data in artists.items():
            if artist_id not in node_set:
                nodes.append({
                    'id': artist_id,
                    'name': artist_data['name'],
                    'type': 'artist', 
                    'size': min(30 + len(artist_data['albums']) * 3, 60),
                    'color': _self.entity_colors['artist']
                })
                node_set.add(artist_id)
                
                # Connect artist to albums (local relationships only)
                for album_id in artist_data['albums'][:10]:  # Limit connections for performance
                    edges.append({'source': artist_id, 'target': album_id})
        
        # Process tracks (sample for performance, no API calls)
        track_sample = list(tracks)[:min(len(tracks), max_nodes // 2)]
        
        for track in track_sample:
            track_id = f"track_{track['id']}"
            album_id = f"album_{track['album_id']}"
            
            if track_id not in node_set:
                # Track size based on length (local metadata only)
                length_size = min(track['length'] / 10000, 10) if track['length'] else 5
                
                nodes.append({
                    'id': track_id,
                    'name': track['title'][:30],  # Truncate for performance
                    'type': 'track',
                    'size': 15 + length_size,
                    'color': _self.entity_colors['track']
                })
                node_set.add(track_id)
                
                # Connect track to album (local relationship only)
                edges.append({'source': track_id, 'target': album_id})
        
        build_time = time.time() - start_time
        
        return {
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'node_count': len(nodes),
                'edge_count': len(edges),
                'build_time': build_time,
                'data_source': 'local_only'
            }
        }
    
    def create_plotly_graph(self, graph_data: Dict) -> go.Figure:
        """Create Plotly visualization - optimized for speed."""
        nodes = graph_data['nodes']
        edges = graph_data['edges']
        
        if not nodes:
            fig = go.Figure()
            fig.add_annotation(text="No data available", showarrow=False, 
                             x=0.5, y=0.5, xref="paper", yref="paper")
            return fig
            
        # Fast layout for performance
        G = nx.Graph()
        G.add_nodes_from([n['id'] for n in nodes])
        G.add_edges_from([(e['source'], e['target']) for e in edges])
        
        # Choose layout based on size for optimal performance
        node_count = len(nodes)
        if node_count > 1000:
            pos = nx.random_layout(G, seed=42)  # Fastest for large graphs
        elif node_count > 500:
            pos = nx.spring_layout(G, k=0.5, iterations=20)  # Balanced
        else:
            pos = nx.spring_layout(G, k=1, iterations=50)  # Best quality for small graphs
            
        # Create traces efficiently
        edge_trace = go.Scatter(
            x=[], y=[], mode='lines', line=dict(width=0.5, color='#888'),
            hoverinfo='none', showlegend=False
        )
        
        # Batch process edges for performance
        for edge in edges:
            if edge['source'] in pos and edge['target'] in pos:
                x0, y0 = pos[edge['source']]
                x1, y1 = pos[edge['target']]
                edge_trace['x'] += (x0, x1, None)
                edge_trace['y'] += (y0, y1, None)
        
        # Create node traces by type for better performance
        node_traces = {}
        for node in nodes:
            node_type = node['type']
            if node_type not in node_traces:
                node_traces[node_type] = go.Scatter(
                    x=[], y=[], mode='markers+text',
                    marker=dict(size=[], color=node['color'], opacity=0.8),
                    text=[], textposition="middle center",
                    name=node_type.title(),
                    hovertemplate=f'<b>%{{text}}</b><br>Type: {node_type}<extra></extra>'
                )
            
            if node['id'] in pos:
                x, y = pos[node['id']]
                node_traces[node_type]['x'] += (x,)
                node_traces[node_type]['y'] += (y,)
                node_traces[node_type]['marker']['size'] += (node['size'],)
                node_traces[node_type]['text'] += (node['name'],)
        
        # Build figure efficiently
        fig = go.Figure(data=[edge_trace] + list(node_traces.values()))
        
        fig.update_layout(
            title=f"Music Universe - {node_count:,} nodes (Local Data Only)",
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[
                dict(text=f"Built in {graph_data['stats']['build_time']:.2f}s", 
                     showarrow=False, xref="paper", yref="paper", 
                     x=0.005, y=-0.002, xanchor='left', font=dict(size=10))
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white'
        )
        
        return fig

def main():
    """Streamlit app for fast graph exploration."""
    st.set_page_config(page_title="LinerNodes Fast Graph", layout="wide")
    
    st.title("🚀 LinerNodes Fast Graph Explorer")
    st.caption("Local data only - No external API calls - Optimized for speed")
    
    # Initialize explorer
    if 'explorer' not in st.session_state:
        st.session_state.explorer = FastMusicGraphExplorer()
    
    explorer = st.session_state.explorer
    
    # Performance controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        max_nodes = st.slider("Maximum Nodes", 100, 10000, 2000, 100,
                            help="Adjust for performance vs completeness")
    
    with col2:
        if st.button("🔄 Refresh Graph", help="Reload with current settings"):
            st.cache_data.clear()
    
    with col3:
        st.metric("Mode", "Local Only", "⚡ Fast")
    
    # Generate and display graph
    try:
        with st.spinner("Building graph from local data..."):
            graph_data = explorer.get_graph_data(max_nodes)
            
        if graph_data['stats']['node_count'] == 0:
            st.warning("No data found. Check your music database.")
            return
            
        # Display stats
        stats = graph_data['stats']
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Nodes", f"{stats['node_count']:,}")
        with col2:
            st.metric("Edges", f"{stats['edge_count']:,}")
        with col3:
            st.metric("Build Time", f"{stats['build_time']:.2f}s")
        with col4:
            st.metric("Performance", "🚀 Fast" if stats['build_time'] < 2 else "⚠️ Slow")
        
        # Create and display graph
        fig = explorer.create_plotly_graph(graph_data)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
        
        # Performance tips
        if stats['build_time'] > 5:
            st.info("💡 Tip: Reduce max nodes or check database performance if graph building is slow")
            
    except Exception as e:
        st.error(f"Error building graph: {str(e)}")
        st.code(str(e))

if __name__ == "__main__":
    main()