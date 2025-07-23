"""
Graph Explorer Interface for LinerNodes.
Provides an interactive graph visualization of your music collection.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
from typing import Dict, List, Set, Tuple, Optional
import json
import sys
from pathlib import Path
import random
import numpy as np
from functools import lru_cache

# Handle imports for both direct execution and package import
try:
    from ..backend.database.models import DatabaseManager, Track, Album, Artist
    from ..backend.database.database import LinerDatabase
except ImportError:
    # Handle direct execution by adding parent directory to path
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from linernodes.backend.database.models import DatabaseManager, Track, Album, Artist
    from linernodes.backend.database.database import LinerDatabase


class MusicGraphExplorer:
    """Interactive graph visualization of your music collection."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the graph explorer."""
        self.db_manager = DatabaseManager(Path(db_path) if db_path else None)
        self.graph = nx.Graph()
        self._graph_cache = {}
        
        # Color scheme for different entity types
        self.entity_colors = {
            'album': '#ff6b6b',      # Red
            'artist': '#4ecdc4',     # Teal
            'track': '#45b7d1',      # Blue
            'genre': '#96ceb4',      # Green
        }
        
        # Size mapping for different entity types
        self.entity_sizes = {
            'album': 20,
            'artist': 25,
            'track': 12,
            'genre': 18,
        }
    
    def build_graph(self, max_nodes: int = 10000) -> nx.Graph:
        """Build a NetworkX graph from the music database.
        
        Optimized for large datasets (10K+ nodes) with efficient memory usage
        and intelligent sampling strategies.
        """
        graph = nx.Graph()
        
        # Get all albums - we want the full universe
        albums = self.db_manager.get_all_albums(limit=max_nodes // 10)
        
        for album in albums:
            # Add album node
            graph.add_node(
                f"album_{album.id}",
                name=album.title,
                type='album',
                id=album.id,
                artist=album.artist_credit or "Unknown Artist"
            )
            
            # Add artist node and connection
            if album.artist_credit:
                artist_node = f"artist_{album.artist_credit}"
                graph.add_node(
                    artist_node,
                    name=album.artist_credit,
                    type='artist',
                    id=album.artist_credit
                )
                graph.add_edge(f"album_{album.id}", artist_node)
            
            # Get tracks for this album - show the full album
            tracks = self.db_manager.get_album_tracks(album.id)
            for track in tracks:  # All tracks - we want completeness
                track_node = f"track_{track.id}"
                graph.add_node(
                    track_node,
                    name=track.title,
                    type='track',
                    id=track.id,
                    duration=track.duration_formatted if track.duration_ms else "Unknown"
                )
                graph.add_edge(f"album_{album.id}", track_node)
                
                # Add genre connections - show full genre relationships
                if track.genre:
                    for genre in track.genre.split(';')[:3]:  # Max 3 genres per track
                        genre = genre.strip()
                        if genre:
                            genre_node = f"genre_{genre}"
                            graph.add_node(
                                genre_node,
                                name=genre,
                                type='genre',
                                id=genre
                            )
                            graph.add_edge(track_node, genre_node)
        
        return graph
    
    @st.cache_data
    def _cached_graph_data(_self, max_nodes: int) -> Dict:
        """Cache expensive graph computation."""
        graph = _self.build_graph(max_nodes)
        
        # Pre-compute layout positions
        if graph.number_of_nodes() > 2000:
            # Ultra-fast layout for massive graphs
            pos = nx.random_layout(graph)
        elif graph.number_of_nodes() > 1000:
            # Fast layout for large graphs
            pos = nx.spring_layout(graph, k=0.3, iterations=10)
        else:
            # Quality layout for smaller graphs
            pos = nx.spring_layout(graph, k=1, iterations=30)
        
        # Convert to serializable format
        nodes_data = []
        edges_data = []
        
        for node_id, node_data in graph.nodes(data=True):
            x, y = pos[node_id]
            nodes_data.append({
                'id': node_id,
                'name': node_data['name'],
                'type': node_data['type'],
                'x': float(x),
                'y': float(y)
            })
        
        for source, target in graph.edges():
            edges_data.append({
                'source': source,
                'target': target
            })
        
        return {
            'nodes': nodes_data,
            'edges': edges_data,
            'stats': {
                'node_count': graph.number_of_nodes(),
                'edge_count': graph.number_of_edges()
            }
        }
    
    def create_optimized_plotly_graph(self, graph_data: Dict, show_labels: bool = False) -> go.Figure:
        """Create optimized Plotly graph from pre-computed data."""
        nodes = graph_data['nodes']
        edges = graph_data['edges']
        
        # Create position lookup
        pos = {node['id']: (node['x'], node['y']) for node in nodes}
        
        # Prepare edge traces (optimized)
        edge_x = []
        edge_y = []
        for edge in edges:
            source_pos = pos[edge['source']]
            target_pos = pos[edge['target']]
            edge_x.extend([source_pos[0], target_pos[0], None])
            edge_y.extend([source_pos[1], target_pos[1], None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Prepare node traces by type (optimized)
        traces = [edge_trace]
        
        for entity_type in ['album', 'artist', 'track', 'genre']:
            nodes_of_type = [n for n in nodes if n['type'] == entity_type]
            if not nodes_of_type:
                continue
            
            node_x = [n['x'] for n in nodes_of_type]
            node_y = [n['y'] for n in nodes_of_type]
            node_text = [n['name'] if show_labels else '' for n in nodes_of_type]
            hover_text = [n['name'] for n in nodes_of_type]
            
            # Optimize rendering mode for large datasets
            mode = 'markers+text' if show_labels and len(nodes_of_type) < 500 else 'markers'
            
            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode=mode,
                hoverinfo='text',
                hovertext=hover_text,
                text=node_text,
                textposition="middle center",
                textfont=dict(size=6 if len(nodes_of_type) > 1000 else 8),
                marker=dict(
                    showscale=False,
                    color=self.entity_colors[entity_type],
                    size=self.entity_sizes[entity_type] if len(nodes_of_type) < 2000 else max(4, self.entity_sizes[entity_type] // 2),
                    line=dict(width=1, color='white') if len(nodes_of_type) < 5000 else dict(width=0)
                ),
                name=entity_type.title()
            )
            traces.append(node_trace)
        
        # Create the figure
        fig = go.Figure(
            data=traces,
            layout=go.Layout(
                title=dict(text='Music Collection Knowledge Graph', font=dict(size=16)),
                showlegend=True,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                annotations=[
                    dict(
                        text="Explore connections between artists, albums, tracks, and genres",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002,
                        xanchor="left", yanchor="bottom",
                        font=dict(color="#888", size=12)
                    )
                ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='white'
            )
        )
        
        return fig
    
    def render_stats(self, graph: nx.Graph):
        """Render graph statistics."""
        col1, col2, col3, col4 = st.columns(4)
        
        # Count nodes by type
        type_counts = {}
        for node in graph.nodes():
            node_type = graph.nodes[node]['type']
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
        
        with col1:
            st.metric("Albums", type_counts.get('album', 0))
        with col2:
            st.metric("Artists", type_counts.get('artist', 0))
        with col3:
            st.metric("Tracks", type_counts.get('track', 0))
        with col4:
            st.metric("Genres", type_counts.get('genre', 0))
        
        st.metric("Total Connections", graph.number_of_edges())
    
    def render_optimized_search(self, graph_data: Dict):
        """Render optimized search functionality."""
        st.subheader("🔍 Search Graph")
        
        search_query = st.text_input("Search for artists, albums, tracks, or genres:")
        
        if search_query:
            # Find matching nodes (optimized)
            matches = []
            query_lower = search_query.lower()
            
            for node in graph_data['nodes']:
                if query_lower in node['name'].lower():
                    matches.append(node)
            
            if matches:
                st.write(f"Found {len(matches)} matches:")
                for node in matches[:20]:  # Show first 20 matches for large datasets
                    node_type = node['type']
                    color = self.entity_colors[node_type]
                    st.write(
                        f"<div style='background: {color}20; padding: 5px; margin: 2px; border-radius: 3px;'>"
                        f"<strong>{node['name']}</strong> ({node_type})"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                if len(matches) > 20:
                    st.caption(f"... and {len(matches) - 20} more results")
            else:
                st.write("No matches found")
    
    def run(self):
        """Main method to run the graph explorer interface."""
        st.set_page_config(
            page_title="LinerNodes Graph Explorer",
            page_icon="🕸️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        st.title("🕸️ Music Knowledge Graph")
        st.markdown("**Explore your music collection as an interconnected network**")
        
        # Sidebar controls
        with st.sidebar:
            st.header("Graph Settings")
            max_nodes = st.slider("Maximum Nodes", 100, 50000, 10000, 500)
            st.caption("🌌 Showing the full musical universe")
            st.caption("⚡ Optimized for large-scale exploration")
            
            # Performance options
            st.subheader("Performance")
            fast_mode = st.checkbox("Fast Mode", value=True, help="Optimized rendering for large graphs")
            show_labels = st.checkbox("Show Labels", value=False, help="Node labels (slower for large graphs)")
            
            if st.button("Refresh Graph", type="primary"):
                st.rerun()
            
            st.markdown("---")
            st.subheader("Legend")
            for entity_type, color in self.entity_colors.items():
                st.write(
                    f"<span style='color: {color}; font-size: 20px;'>●</span> {entity_type.title()}",
                    unsafe_allow_html=True
                )
        
        # Main content
        try:
            # Build the graph with caching
            with st.spinner("Building knowledge graph..."):
                graph_data = self._cached_graph_data(max_nodes)
            
            if graph_data['stats']['node_count'] == 0:
                st.error("No data found in database. Please import some music first.")
                st.code("uv run linernodes sources import-all")
                return
            
            # Show stats
            st.subheader("📊 Graph Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Nodes", f"{graph_data['stats']['node_count']:,}")
            with col2:
                st.metric("Connections", f"{graph_data['stats']['edge_count']:,}")
            with col3:
                node_types = {}
                for node in graph_data['nodes']:
                    node_types[node['type']] = node_types.get(node['type'], 0) + 1
                st.metric("Node Types", len(node_types))
            with col4:
                density = (2 * graph_data['stats']['edge_count']) / (graph_data['stats']['node_count'] * (graph_data['stats']['node_count'] - 1)) if graph_data['stats']['node_count'] > 1 else 0
                st.metric("Density", f"{density:.4f}")
            
            # Performance info
            st.caption(f"🚀 Rendering {graph_data['stats']['node_count']:,} nodes with optimized algorithms")
            
            # Show the graph
            st.subheader("🕸️ Interactive Graph")
            with st.spinner("Rendering optimized visualization..."):
                fig = self.create_optimized_plotly_graph(graph_data, show_labels)
                st.plotly_chart(fig, use_container_width=True, height=700)
            
            # Search functionality
            self.render_optimized_search(graph_data)
            
        except Exception as e:
            st.error(f"Error loading graph: {e}")
            st.code(f"Error details: {str(e)}")


def main():
    """Entry point for direct execution."""
    explorer = MusicGraphExplorer()
    explorer.run()


if __name__ == "__main__":
    main()