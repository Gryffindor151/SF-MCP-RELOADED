#!/usr/bin/env python3
"""
Debug script to see raw MCP server responses
"""

import asyncio
import sys
import json
import subprocess
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.config import config

async def debug_mcp_response():
    """Debug the raw MCP server response"""
    
    print("🔍 Debugging MCP Server Response")
    print("=" * 40)
    
    # Validate config
    errors = config.validate_salesforce_config()
    if errors:
        print(f"❌ Config errors: {errors}")
        return
    
    # Get environment variables
    env_vars = config.get_salesforce_env_vars()
    
    # Build shell command
    env_exports = f"""
export SALESFORCE_CONNECTION_TYPE="{env_vars['SALESFORCE_CONNECTION_TYPE']}"
export SALESFORCE_USERNAME="{env_vars['SALESFORCE_USERNAME']}"
export SALESFORCE_PASSWORD="{env_vars['SALESFORCE_PASSWORD']}"
export SALESFORCE_TOKEN="{env_vars['SALESFORCE_TOKEN']}"
export SALESFORCE_INSTANCE_URL="{env_vars['SALESFORCE_INSTANCE_URL']}"
"""
    
    # Create JSON-RPC request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    json_request = json.dumps(request)
    command = f"{env_exports}echo '{json_request}' | npx @tsmztech/mcp-server-salesforce"
    
    print("📤 Request being sent:")
    print(json.dumps(request, indent=2))
    print()
    
    try:
        # Execute command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"🔧 Command return code: {result.returncode}")
        print()
        
        if result.returncode != 0:
            print("❌ STDERR:")
            print(result.stderr)
            print()
            return
        
        print("📥 Raw STDOUT:")
        print(repr(result.stdout))  # Show exact string with escape chars
        print()
        
        print("📥 Raw STDOUT (formatted):")
        print(result.stdout)
        print()
        
        # Try to parse JSON
        try:
            response = json.loads(result.stdout.strip())
            print("✅ Successfully parsed JSON response:")
            print(json.dumps(response, indent=2))
            print()
            
            # Analyze the response structure
            print("🔍 Response Analysis:")
            print(f"- Response keys: {list(response.keys())}")
            
            if "result" in response:
                result_data = response["result"]
                print(f"- Result type: {type(result_data)}")
                print(f"- Result keys: {list(result_data.keys()) if isinstance(result_data, dict) else 'Not a dict'}")
                
                # Check for tools directly
                if "tools" in result_data:
                    tools = result_data["tools"]
                    print(f"- Tools found directly: {len(tools)}")
                    if tools:
                        print(f"- First tool: {tools[0]}")
                
                # Check for content array
                elif "content" in result_data:
                    content = result_data["content"]
                    print(f"- Content type: {type(content)}")
                    print(f"- Content length: {len(content) if isinstance(content, list) else 'Not a list'}")
                    
                    if isinstance(content, list) and len(content) > 0:
                        first_content = content[0]
                        print(f"- First content keys: {list(first_content.keys()) if isinstance(first_content, dict) else 'Not a dict'}")
                        
                        if "text" in first_content:
                            text_content = first_content["text"]
                            print(f"- Text content preview: {text_content[:200]}...")
                            
                            # Try parsing text as JSON
                            try:
                                parsed_text = json.loads(text_content)
                                print("✅ Text content is valid JSON:")
                                print(json.dumps(parsed_text, indent=2))
                                
                                if "tools" in parsed_text:
                                    tools = parsed_text["tools"]
                                    print(f"✅ Found {len(tools)} tools in text content!")
                                    for i, tool in enumerate(tools[:3]):
                                        print(f"   {i+1}. {tool.get('name', 'Unknown')}")
                                
                            except json.JSONDecodeError as e:
                                print(f"❌ Text content is not valid JSON: {e}")
                
                else:
                    print("❌ No 'tools' or 'content' in result")
                    print(f"- Available keys: {list(result_data.keys())}")
            
            elif "error" in response:
                print(f"❌ Error in response: {response['error']}")
            
            else:
                print("❌ No 'result' or 'error' in response")
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print("Raw output might not be valid JSON")
        
    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_mcp_response()) 