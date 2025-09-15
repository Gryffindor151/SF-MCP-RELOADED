#!/usr/bin/env python3
"""
Test complete LLM integration with natural language responses
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

async def test_natural_language_responses():
    """Test the complete natural language interface"""
    
    print("🚀 Testing Natural Language Interface")
    print("=" * 50)
    
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
        
        # Test queries with natural language responses
        test_queries = [
            "Show me all Technology accounts",
            "What fields are available on Contact?", 
            "Search for objects containing Order",
            "How many accounts do we have?",
            "Describe the Account object"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}️⃣ Query: '{query}'")
            print("-" * 60)
            
            try:
                # Process query and get natural language response
                result = await tool_selector.process_query(query)
                
                if result.get("success"):
                    # Show the natural language response
                    print(f"🤖 Response:")
                    print(f"   {result['natural_response']}")
                    
                    # Show technical details (optional)
                    metadata = result.get("metadata", {})
                    print(f"\n📊 Technical Details:")
                    print(f"   Tool Used: {result.get('tool_used', 'Unknown')}")
                    print(f"   Confidence: {metadata.get('confidence', 0):.2f}")
                    print(f"   Category: {metadata.get('category', 'Unknown')}")
                    
                else:
                    print(f"❌ Error Response:")
                    print(f"   {result['natural_response']}")
                
            except Exception as e:
                print(f"❌ Query failed: {e}")
        
        print(f"\n🎉 Natural Language Interface test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        await mcp_client.close()

async def interactive_mode():
    """Interactive mode for testing queries"""
    
    print("🎮 Interactive Mode - Type 'quit' to exit")
    print("=" * 40)
    
    # Initialize components
    mcp_client = MCPClient()
    tool_selector = ToolSelector(mcp_client)
    
    try:
        await mcp_client.start_server()
        print("✅ Ready for queries!\n")
        
        while True:
            try:
                # Get user input
                user_query = input("💬 Ask me about Salesforce: ").strip()
                
                if user_query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_query:
                    continue
                
                print("🤔 Processing...")
                
                # Process query
                result = await tool_selector.process_query(user_query)
                
                # Show response
                print(f"\n🤖 {result['natural_response']}\n")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")
        
        print("👋 Goodbye!")
        
    finally:
        await mcp_client.close()

async def main():
    """Main function"""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        await interactive_mode()
    else:
        success = await test_natural_language_responses()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main()) 