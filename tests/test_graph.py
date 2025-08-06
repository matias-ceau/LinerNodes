#!/usr/bin/env python3
"""Simple test to verify graph interface works."""

import sys
import time
import subprocess
import requests

def test_graph_interface():
    """Test that the graph interface starts and serves content."""
    print("🧪 Testing graph interface...")
    
    # Start the interface
    process = subprocess.Popen([
        "uv", "run", "linernodes", "interface", "graph", "--port", "8503"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for startup
    print("⏱️  Waiting for interface to start...")
    for i in range(30):  # 30 second timeout
        try:
            response = requests.get("http://localhost:8503", timeout=2)
            if response.status_code == 200:
                print("✅ Graph interface is running!")
                print("🌐 Access at: http://localhost:8503")
                return True
        except:
            time.sleep(1)
            continue
    
    print("❌ Graph interface failed to start within 30 seconds")
    
    # Print any error output
    try:
        stdout, stderr = process.communicate(timeout=1)
        if stderr:
            print("Error output:")
            print(stderr.decode())
    except:
        pass
        
    return False

if __name__ == "__main__":
    success = test_graph_interface()
    sys.exit(0 if success else 1)