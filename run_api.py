#!/usr/bin/env python3
"""
Run the FastAPI server
"""

import uvicorn
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.config import config

if __name__ == "__main__":
    print("🚀 Starting Salesforce Natural Language API")
    print(f"Server: http://{config.API_HOST}:{config.API_PORT}")
    print(f"Docs: http://{config.API_HOST}:{config.API_PORT}/docs")
    print("=" * 50)
    
    uvicorn.run(
        "src.api.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.API_DEBUG
    ) 