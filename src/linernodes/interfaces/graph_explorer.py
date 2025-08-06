"""
Graph Explorer Interface for LinerNodes.
Provides an interactive graph visualization of your music collection.
"""

import streamlit as st
import plotly.graph_objects as go
import networkx as nx
from typing import Dict, Optional
import sys
from pathlib import Path
import time
import psutil
import os

# Handle imports for both direct execution and package import
try:
    from ..backend.database.models import DatabaseManager, Track, Album, Artist
    from ..backend.database.database import LinerDatabase
except ImportError:
    # Handle direct execution by adding parent directory to path
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from linernodes.backend.database.models import DatabaseManager


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
        
        OPTIMIZED: Single bulk query replaces N+1 pattern for 10K+ node performance.
        """
        graph = nx.Graph()
        
        # PERFORMANCE FIX: Single bulk query instead of N+1 album/track queries
        graph_data = self.db_manager.get_graph_data_bulk(limit=max_nodes)
        
        nodes = graph_data['nodes']
        edges = graph_data['edges']
        
        # PERFORMANCE FIX: Bulk operations instead of individual add_node() calls
        node_list = []
        for node in nodes:
            # Add color and size attributes for visualization
            color = self.entity_colors.get(node['type'], '#888888')
            size = self.entity_sizes.get(node['type'], 15)
            
            node_list.append((
                node['id'],
                {
                    'name': node['name'],
                    'type': node['type'],
                    'color': color,
                    'size': size
                }
            ))
        
        # PERFORMANCE FIX: Single bulk node addition
        graph.add_nodes_from(node_list)
        
        # PERFORMANCE FIX: Bulk edge operations instead of individual add_edge() calls
        edge_list = [(edge['source'], edge['target']) for edge in edges]
        graph.add_edges_from(edge_list)
        
        return graph
    
    def _get_graph_data(self, max_nodes: int) -> Dict:
        """PERFORMANCE FIX: Use persistent file cache instead of memory cache."""
        return self.db_manager.get_graph_data_bulk_cached(limit=max_nodes)
    
    def _build_positioned_graph_data(self, cached_data: Dict) -> Dict:
        """Build graph with positions from cached SQL data."""
        # Build NetworkX graph for layout computation only
        graph = self._build_graph_from_cached_data(cached_data)
        
        # Compute layout positions
        pos = self._compute_layout_positions(graph)
        
        # Convert to serializable format with positions
        nodes_data = []
        for node in cached_data['nodes']:
            if node['id'] in pos:
                x, y = pos[node['id']]
                nodes_data.append({
                    'id': node['id'],
                    'name': node['name'],
                    'type': node['type'],
                    'x': float(x),
                    'y': float(y)
                })
        
        edges_data = cached_data['edges']
        
        return {
            'nodes': nodes_data,
            'edges': edges_data,
            'stats': cached_data['stats']
        }
    
    def _build_graph_from_cached_data(self, cached_data: Dict) -> nx.Graph:
        """Build NetworkX graph from cached data."""
        graph = nx.Graph()
        
        nodes = cached_data['nodes']
        edges = cached_data['edges']
        
        # Bulk operations using cached data
        node_list = []
        for node in nodes:
            color = self.entity_colors.get(node['type'], '#888888')
            size = self.entity_sizes.get(node['type'], 15)
            
            node_list.append((
                node['id'],
                {
                    'name': node['name'],
                    'type': node['type'],
                    'color': color,
                    'size': size
                }
            ))
        
        graph.add_nodes_from(node_list)
        edge_list = [(edge['source'], edge['target']) for edge in edges]
        graph.add_edges_from(edge_list)
        
        return graph
    
    def _compute_layout_positions(self, graph: nx.Graph) -> Dict:
        """Compute layout positions with adaptive algorithms."""
        node_count = graph.number_of_nodes()
        
        if node_count > 2000:
            # Ultra-fast layout for massive graphs
            pos = nx.random_layout(graph, seed=42)
        elif node_count > 1000:
            # Fast layout for large graphs  
            pos = nx.spring_layout(graph, k=0.3, iterations=10, seed=42)
        else:
            # Quality layout for smaller graphs
            pos = nx.spring_layout(graph, k=1, iterations=30, seed=42)
        
        return pos
    
    def get_performance_metrics(self) -> Dict:
        """Get current system performance metrics."""
        process = psutil.Process(os.getpid())
        
        return {
            'cpu_percent': process.cpu_percent(interval=0.1),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'memory_percent': process.memory_percent(),
            'threads': process.num_threads()
        }
    
    def get_cache_metrics(self) -> Dict:
        """Get graph cache metrics."""
        cache_path = self.db_manager.get_graph_cache_path()
        
        if cache_path.exists():
            stat = cache_path.stat()
            return {
                'exists': True,
                'size_mb': stat.st_size / 1024 / 1024,
                'modified': stat.st_mtime,
                'age_minutes': (time.time() - stat.st_mtime) / 60
            }
        else:
            return {
                'exists': False,
                'size_mb': 0,
                'modified': 0,
                'age_minutes': 0
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
            
            # Performance monitoring
            st.subheader("⚡ Performance")
            
            # Real-time metrics
            perf_metrics = self.get_performance_metrics()
            cache_metrics = self.get_cache_metrics()
            
            col1, col2 = st.columns(2)
            with col1:
                cpu_color = "🔴" if perf_metrics['cpu_percent'] > 50 else "🟡" if perf_metrics['cpu_percent'] > 20 else "🟢"
                st.metric("CPU Usage", f"{perf_metrics['cpu_percent']:.1f}%", delta=None, help=f"{cpu_color} Current process CPU usage")
                
            with col2:
                memory_color = "🔴" if perf_metrics['memory_mb'] > 500 else "🟡" if perf_metrics['memory_mb'] > 200 else "🟢"
                st.metric("Memory", f"{perf_metrics['memory_mb']:.0f} MB", delta=None, help=f"{memory_color} Current process memory usage")
            
            # Cache status
            if cache_metrics['exists']:
                st.success(f"✅ Graph Cache Active ({cache_metrics['size_mb']:.1f} MB, {cache_metrics['age_minutes']:.0f}min old)")
            else:
                st.warning("⚠️ No Graph Cache - Will build on first load")
            
            # Performance options
            fast_mode = st.checkbox("Fast Mode", value=True, help="Optimized rendering for large graphs")
            show_labels = st.checkbox("Show Labels", value=False, help="Node labels (slower for large graphs)")
            
            if st.button("🔄 Refresh Graph", type="primary"):
                self.db_manager.invalidate_graph_cache()
                st.rerun()
                
            if st.button("🗑️ Clear Cache"):
                self.db_manager.invalidate_graph_cache()
                st.success("Cache cleared!")
            
            st.markdown("---")
            st.subheader("Legend")
            for entity_type, color in self.entity_colors.items():
                st.write(
                    f"<span style='color: {color}; font-size: 20px;'>●</span> {entity_type.title()}",
                    unsafe_allow_html=True
                )
        
        # Main content
        try:
            # Build the graph with persistent caching and timing
            start_time = time.time()
            with st.spinner("Loading knowledge graph..."):
                graph_data = self._get_graph_data(max_nodes)
                data_load_time = time.time() - start_time
                
                layout_start = time.time()
                positioned_data = self._build_positioned_graph_data(graph_data)
                layout_time = time.time() - layout_start
                
                total_time = time.time() - start_time
            
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
                render_start = time.time()
                fig = self.create_optimized_plotly_graph(positioned_data, show_labels)
                render_time = time.time() - render_start
                st.plotly_chart(fig, use_container_width=True, height=700)
                
            # Performance metrics display
            st.subheader("📊 Performance Metrics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📊 Nodes", f"{graph_data['stats']['node_count']:,}")
            with col2:
                st.metric("🔗 Edges", f"{graph_data['stats']['edge_count']:,}")
            with col3:
                load_color = "🟢" if data_load_time < 1 else "🟡" if data_load_time < 3 else "🔴"
                st.metric("⚡ Data Load", f"{data_load_time:.2f}s", help=f"{load_color} Cache/database query time")
            with col4:
                total_render_time = layout_time + render_time
                render_color = "🟢" if total_render_time < 2 else "🟡" if total_render_time < 5 else "🔴"
                st.metric("🎨 Render Time", f"{total_render_time:.2f}s", help=f"{render_color} Layout + visualization time")
            
            # Overall performance status
            total_time = data_load_time + layout_time + render_time
            if total_time < 3:
                st.success(f"🚀 Excellent performance: {total_time:.2f}s total rendering time")
            elif total_time < 8:
                st.info(f"⚡ Good performance: {total_time:.2f}s total rendering time")  
            else:
                st.warning(f"🐌 Consider reducing node count: {total_time:.2f}s total rendering time")
            
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