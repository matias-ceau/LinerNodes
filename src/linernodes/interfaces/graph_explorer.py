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
    
    def build_graph(self, max_nodes: int = 200) -> nx.Graph:
        """Build a NetworkX graph from the music database."""
        graph = nx.Graph()
        
        # Get albums and their basic info
        albums = self.db_manager.get_all_albums(limit=min(max_nodes // 4, 50))
        
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
            
            # Get tracks for this album
            tracks = self.db_manager.get_album_tracks(album.id)
            for track in tracks[:10]:  # Limit tracks per album
                track_node = f"track_{track.id}"
                graph.add_node(
                    track_node,
                    name=track.title,
                    type='track',
                    id=track.id,
                    duration=track.duration_formatted if track.duration_ms else "Unknown"
                )
                graph.add_edge(f"album_{album.id}", track_node)
                
                # Add genre connections if available
                if track.genre:
                    for genre in track.genre.split(';')[:2]:  # Max 2 genres per track
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
    
    def create_plotly_graph(self, graph: nx.Graph) -> go.Figure:
        """Create a Plotly interactive graph visualization."""
        # Use spring layout for better node positioning
        pos = nx.spring_layout(graph, k=1, iterations=50)
        
        # Prepare edge traces
        edge_x = []
        edge_y = []
        for edge in graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Prepare node traces by type
        traces = [edge_trace]
        
        for entity_type in ['album', 'artist', 'track', 'genre']:
            nodes_of_type = [n for n in graph.nodes() if graph.nodes[n]['type'] == entity_type]
            if not nodes_of_type:
                continue
            
            node_x = [pos[node][0] for node in nodes_of_type]
            node_y = [pos[node][1] for node in nodes_of_type]
            node_text = [graph.nodes[node]['name'] for node in nodes_of_type]
            
            # Create hover text with additional info
            hover_text = []
            for node in nodes_of_type:
                node_data = graph.nodes[node]
                if entity_type == 'track':
                    hover_text.append(f"{node_data['name']}<br>Duration: {node_data.get('duration', 'Unknown')}")
                elif entity_type == 'album':
                    hover_text.append(f"{node_data['name']}<br>Artist: {node_data.get('artist', 'Unknown')}")
                else:
                    hover_text.append(node_data['name'])
            
            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                hoverinfo='text',
                hovertext=hover_text,
                text=node_text,
                textposition="middle center",
                textfont=dict(size=8),
                marker=dict(
                    showscale=False,
                    color=self.entity_colors[entity_type],
                    size=self.entity_sizes[entity_type],
                    line=dict(width=2, color='white')
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
    
    def render_search(self, graph: nx.Graph):
        """Render search functionality."""
        st.subheader("🔍 Search Graph")
        
        search_query = st.text_input("Search for artists, albums, tracks, or genres:")
        
        if search_query:
            # Find matching nodes
            matches = []
            for node in graph.nodes():
                node_data = graph.nodes[node]
                if search_query.lower() in node_data['name'].lower():
                    matches.append((node, node_data))
            
            if matches:
                st.write(f"Found {len(matches)} matches:")
                for node_id, node_data in matches[:10]:  # Show first 10 matches
                    node_type = node_data['type']
                    color = self.entity_colors[node_type]
                    st.write(
                        f"<div style='background: {color}20; padding: 5px; margin: 2px; border-radius: 3px;'>"
                        f"<strong>{node_data['name']}</strong> ({node_type})"
                        f"</div>",
                        unsafe_allow_html=True
                    )
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
            max_nodes = st.slider("Maximum Nodes", 50, 500, 200, 50)
            
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
            # Build the graph
            with st.spinner("Building knowledge graph..."):
                graph = self.build_graph(max_nodes)
            
            if graph.number_of_nodes() == 0:
                st.error("No data found in database. Please import some music first.")
                st.code("uv run linernodes sources import-all")
                return
            
            # Show stats
            st.subheader("📊 Graph Statistics")
            self.render_stats(graph)
            
            # Show the graph
            st.subheader("🕸️ Interactive Graph")
            with st.spinner("Rendering graph..."):
                fig = self.create_plotly_graph(graph)
                st.plotly_chart(fig, use_container_width=True, height=600)
            
            # Search functionality
            self.render_search(graph)
            
        except Exception as e:
            st.error(f"Error loading graph: {e}")
            st.code(f"Error details: {str(e)}")


def main():
    """Entry point for direct execution."""
    explorer = MusicGraphExplorer()
    explorer.run()


if __name__ == "__main__":
    main()