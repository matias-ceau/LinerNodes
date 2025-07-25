#!/usr/bin/env python3
"""Test graph data generation directly."""

from src.linernodes.interfaces.graph_explorer import MusicGraphExplorer

def test_graph_generation():
    """Test if we can generate graph data."""
    print("🧪 Testing graph data generation...")
    
    try:
        explorer = MusicGraphExplorer()
        print("✅ Graph explorer initialized")
        
        graph_data = explorer._cached_graph_data(50)
        print("✅ Graph data generated successfully!")
        print(f"   - Nodes: {graph_data['stats']['node_count']}")
        print(f"   - Edges: {graph_data['stats']['edge_count']}")
        
        if graph_data['stats']['node_count'] > 0:
            sample_nodes = [n['name'] for n in graph_data['nodes'][:3]]
            print(f"   - Sample nodes: {sample_nodes}")
            return True
        else:
            print("   - No nodes found - database might be empty")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_graph_generation()
    exit(0 if success else 1)