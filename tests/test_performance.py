#!/usr/bin/env python3
"""
Performance test for LinerNodes graph rendering.
Tests various node counts to measure performance scaling.
"""

import time
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from linernodes.interfaces.graph_explorer import MusicGraphExplorer

def test_performance(node_counts):
    """Test graph performance at different scales."""
    print("🔬 LinerNodes Graph Performance Testing")
    print("=" * 50)
    
    explorer = MusicGraphExplorer()
    results = []
    
    for max_nodes in node_counts:
        print(f"\n🧪 Testing with max_nodes = {max_nodes:,}")
        
        start_time = time.time()
        try:
            graph_data = explorer._cached_graph_data(max_nodes)
            end_time = time.time()
            
            duration = end_time - start_time
            actual_nodes = graph_data['stats']['node_count']
            actual_edges = graph_data['stats']['edge_count']
            
            print(f"   ✅ Generated in {duration:.2f}s")
            print(f"   📊 Nodes: {actual_nodes:,} | Edges: {actual_edges:,}")
            
            # Performance metrics
            nodes_per_second = actual_nodes / duration if duration > 0 else 0
            print(f"   ⚡ Performance: {nodes_per_second:.0f} nodes/second")
            
            results.append({
                'max_nodes': max_nodes,
                'actual_nodes': actual_nodes,
                'actual_edges': actual_edges,
                'duration': duration,
                'nodes_per_second': nodes_per_second
            })
            
            # Memory efficiency indicator
            if actual_nodes > 0:
                edge_ratio = actual_edges / actual_nodes
                print(f"   🕸️  Connectivity: {edge_ratio:.1f} edges per node")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results.append({
                'max_nodes': max_nodes,
                'error': str(e)
            })
    
    return results

def performance_summary(results):
    """Print performance summary."""
    print("\n" + "=" * 50)
    print("📈 PERFORMANCE SUMMARY")
    print("=" * 50)
    
    successful_tests = [r for r in results if 'error' not in r]
    
    if successful_tests:
        fastest = max(successful_tests, key=lambda x: x['nodes_per_second'])
        largest = max(successful_tests, key=lambda x: x['actual_nodes'])
        
        print(f"🏆 Fastest: {fastest['nodes_per_second']:.0f} nodes/sec at {fastest['max_nodes']:,} max nodes")
        print(f"🏆 Largest: {largest['actual_nodes']:,} nodes with {largest['actual_edges']:,} edges")
        
        if largest['actual_nodes'] >= 10000:
            print("✅ MEETS 10K+ NODE REQUIREMENT!")
        else:
            print(f"📊 Current max: {largest['actual_nodes']:,} nodes (database limited)")
            
        # Performance scaling analysis
        if len(successful_tests) > 1:
            small = min(successful_tests, key=lambda x: x['actual_nodes'])
            large = max(successful_tests, key=lambda x: x['actual_nodes'])
            
            if large['actual_nodes'] > small['actual_nodes']:
                scaling_factor = large['duration'] / small['duration']
                node_ratio = large['actual_nodes'] / small['actual_nodes']
                efficiency = node_ratio / scaling_factor
                
                print(f"📈 Scaling efficiency: {efficiency:.2f} (1.0 = linear, >1.0 = super-linear)")
    
    failed_tests = [r for r in results if 'error' in r]
    if failed_tests:
        print(f"\n❌ {len(failed_tests)} tests failed")

def main():
    """Run comprehensive performance testing."""
    # Test at various scales
    node_counts = [
        500,      # Small test
        1000,     # Medium test  
        2000,     # Large test
        5000,     # Very large test
        10000,    # Target requirement
        20000,    # Beyond requirement
    ]
    
    print("🎵 Testing LinerNodes graph performance at scale")
    print("📋 This tests the 'no limiting nodes' requirement")
    print("🎯 Target: Handle 10K+ nodes efficiently\n")
    
    results = test_performance(node_counts)
    performance_summary(results)
    
    print("\n🌐 Graph interface running at: http://localhost:8507")
    print("🔧 Use the 'Maximum Nodes' slider to test different scales interactively")

if __name__ == "__main__":
    main()