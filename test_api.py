#!/usr/bin/env python3
"""
Test the FastAPI endpoints
"""

import requests
import json
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.config import config

def test_api():
    """Test API endpoints"""
    
    base_url = f"http://{config.API_HOST}:{config.API_PORT}"
    token = config.API_BEARER_TOKEN or "test-token"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing API Endpoints")
    print("=" * 30)
    
    # Test health
    print("\n1️⃣ Health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test query
    print("\n2️⃣ Query test...")
    try:
        payload = {"query": "Show me all Technology accounts"}
        response = requests.post(f"{base_url}/query", headers=headers, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result['success']}")
            print(f"Response: {result['natural_response'][:100]}...")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Query test failed: {e}")

if __name__ == "__main__":
    test_api() 