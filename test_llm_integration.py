#!/usr/bin/env python3
"""
Test LLM integration with tool selection
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.mcp.client import MCPClient
from src.llm.tool_selector import ToolSelector
from src.core.config import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_llm_integration():
    """Test the complete LLM integration"""
    
    print("🚀 Testing LLM Integration")
    print("=" * 40)
    
    # Validate config
    sf_errors = config.validate_salesforce_config()
    llm_errors = config.validate_llm_config()
    
    if sf_errors or llm_errors:
        print(f"❌ Config errors: {sf_errors + llm_errors}")
        return False
    
    print("✅ Configuration validated")
    
    # Initialize components
    mcp_client = MCPClient()
    tool_selector = ToolSelector(mcp_client)
    
    try:
        # Start MCP client
        await mcp_client.start_server()
        print("✅ MCP client started")
        
        # Test queries
        test_queries = [
            "Show me all Technology accounts"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}️⃣ Testing Query: '{query}'")
            print("-" * 50)
            
            try:
                # Select tool using LLM
                result = await tool_selector.select_tool(query)
                
                if result.get("success"):
                    print(f"✅ Tool Selected: {result['tool_name']}")
                    print(f"   Parameters: {result['parameters']}")
                    print(f"   Reasoning: {result['reasoning']}")
                    print(f"   Confidence: {result['confidence']:.2f}")
                    print(f"   Category: {result['selected_tool_info']['category']}")
                    
                    # Test actual tool execution
                    if result['tool_name'] and result['parameters']:
                        print("   🔧 Executing tool...")
                        tool_result = await mcp_client.call_tool(
                            result['tool_name'], 
                            result['parameters']
                        )
                        print(f"   ✅ Tool executed successfully")
                        print(f"   📊 Result preview: {str(tool_result)[:100]}...")
                    
                else:
                    print(f"❌ Tool selection failed: {result.get('error')}")
                
            except Exception as e:
                print(f"❌ Query failed: {e}")
        
        # Show statistics
        print(f"\n📊 Tool Selector Statistics")
        print("-" * 30)
        stats = await tool_selector.get_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        print("\n🎉 LLM Integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        await mcp_client.close()

if __name__ == "__main__":
    success = asyncio.run(test_llm_integration())
    sys.exit(0 if success else 1) 