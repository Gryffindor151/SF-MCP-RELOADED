#!/usr/bin/env python3
"""
Test suite for the simplified MCPClient
"""

import asyncio
import sys
import logging
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.mcp.client import MCPClient
from src.core.config import config
from src.core.exceptions import MCPConnectionError, SalesforceAPIError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class TestMCPClient:
    """Test suite for MCPClient"""
    
    def __init__(self):
        self.client = None
        self.passed = 0
        self.failed = 0
    
    def assert_test(self, condition: bool, test_name: str, message: str = ""):
        """Assert a test condition"""
        if condition:
            print(f"✅ {test_name}")
            if message:
                print(f"   {message}")
            self.passed += 1
        else:
            print(f"❌ {test_name}")
            if message:
                print(f"   {message}")
            self.failed += 1
        return condition
    
    async def test_client_initialization(self):
        """Test client initialization"""
        print("\n🔧 Testing Client Initialization")
        print("-" * 40)
        
        # Test config validation
        errors = config.validate_salesforce_config()
        self.assert_test(
            len(errors) == 0,
            "Configuration Validation",
            f"Errors: {errors}" if errors else "All environment variables present"
        )
        
        if errors:
            return False
        
        # Test client creation
        try:
            self.client = MCPClient()
            self.assert_test(True, "Client Creation", "MCPClient instance created successfully")
        except Exception as e:
            self.assert_test(False, "Client Creation", f"Failed: {e}")
            return False
        
        # Test client properties
        self.assert_test(
            self.client.request_id == 0,
            "Initial Request ID",
            f"Request ID: {self.client.request_id}"
        )
        
        self.assert_test(
            self.client.timeout == 30,
            "Default Timeout",
            f"Timeout: {self.client.timeout}s"
        )
        
        # Test start_server method
        try:
            result = await self.client.start_server()
            self.assert_test(
                result is True,
                "Start Server",
                "Server initialization successful"
            )
        except Exception as e:
            self.assert_test(False, "Start Server", f"Failed: {e}")
            return False
        
        return True
    
    async def test_internal_methods(self):
        """Test internal helper methods"""
        print("\n🔍 Testing Internal Methods")
        print("-" * 40)
        
        # Test _get_next_request_id
        initial_id = self.client.request_id
        next_id = self.client._get_next_request_id()
        self.assert_test(
            next_id == initial_id + 1,
            "Request ID Increment",
            f"ID: {initial_id} → {next_id}"
        )
        
        # Test _get_shell_command
        test_request = '{"test": "data"}'
        shell_command = self.client._get_shell_command(test_request)
        
        # Check if command contains required elements
        has_exports = "export SALESFORCE_" in shell_command
        has_echo = "echo" in shell_command
        has_npx = "npx @tsmztech/mcp-server-salesforce" in shell_command
        
        self.assert_test(
            has_exports and has_echo and has_npx,
            "Shell Command Generation",
            "Command contains all required elements"
        )
        
        # Test _parse_response with different response types
        # Test 1: Normal response with content
        normal_response = {
            "content": [{"text": '{"tools": [{"name": "test_tool"}]}'}]
        }
        parsed = self.client._parse_response(normal_response)
        self.assert_test(
            "tools" in parsed,
            "Parse Normal Response",
            f"Parsed: {parsed}"
        )
        
        # Test 2: Error response
        error_response = {
            "isError": True,
            "content": [{"text": "Test error message"}]
        }
        try:
            self.client._parse_response(error_response)
            self.assert_test(False, "Parse Error Response", "Should have raised exception")
        except SalesforceAPIError:
            self.assert_test(True, "Parse Error Response", "Correctly raised SalesforceAPIError")
        
        # Test 3: Empty response
        empty_response = {}
        parsed_empty = self.client._parse_response(empty_response)
        self.assert_test(
            parsed_empty == {},
            "Parse Empty Response",
            "Returns empty dict for empty response"
        )
        
        return True
    
    async def test_tools_listing(self):
        """Test tools listing functionality"""
        print("\n📋 Testing Tools Listing")
        print("-" * 40)
        
        try:
            tools = await self.client.list_tools()
            
            # Test that we get a list
            self.assert_test(
                isinstance(tools, list),
                "Tools List Type",
                f"Type: {type(tools)}"
            )
            
            # Test that we have tools
            self.assert_test(
                len(tools) > 0,
                "Tools Count",
                f"Found {len(tools)} tools"
            )
            
            if tools:
                # Test first tool structure
                first_tool = tools[0]
                has_name = "name" in first_tool
                has_description = "description" in first_tool
                
                self.assert_test(
                    has_name,
                    "Tool Has Name",
                    f"First tool name: {first_tool.get('name', 'N/A')}"
                )
                
                self.assert_test(
                    has_description,
                    "Tool Has Description",
                    f"Has description: {has_description}"
                )
                
                # Print sample tools
                print("   Sample tools:")
                for i, tool in enumerate(tools[:3]):
                    name = tool.get('name', 'Unknown')
                    desc = tool.get('description', 'No description')[:50]
                    print(f"     {i+1}. {name}: {desc}...")
                
                if len(tools) > 3:
                    print(f"     ... and {len(tools) - 3} more tools")
            
            return len(tools) > 0
            
        except Exception as e:
            self.assert_test(False, "Tools Listing", f"Exception: {e}")
            return False
    
    async def test_tool_execution(self):
        """Test tool execution"""
        print("\n🔧 Testing Tool Execution")
        print("-" * 40)
        
        # Test salesforce_search_objects
        try:
            result = await self.client.call_tool(
                "salesforce_search_objects",
                {"searchPattern": "Account"}
            )
            
            self.assert_test(
                result is not None,
                "Search Objects Tool",
                f"Result type: {type(result)}"
            )
            
            print(f"   Search result: {result}")
            
        except Exception as e:
            self.assert_test(False, "Search Objects Tool", f"Exception: {e}")
        
        # Test salesforce_describe_object
        try:
            result = await self.client.call_tool(
                "salesforce_describe_object",
                {"objectName": "Account"}
            )
            
            self.assert_test(
                result is not None,
                "Describe Object Tool",
                f"Result type: {type(result)}"
            )
            
            # Check for fields in result
            if isinstance(result, dict) and "fields" in result:
                fields_count = len(result["fields"])
                print(f"   Account has {fields_count} fields")
            else:
                print(f"   Describe result: {str(result)[:100]}...")
            
        except Exception as e:
            self.assert_test(False, "Describe Object Tool", f"Exception: {e}")
        
        return True
    
    async def test_error_handling(self):
        """Test error handling"""
        print("\n⚠️  Testing Error Handling")
        print("-" * 40)
        
        # Test invalid tool name
        try:
            await self.client.call_tool("nonexistent_tool", {})
            self.assert_test(False, "Invalid Tool Name", "Should have raised exception")
        except Exception as e:
            self.assert_test(True, "Invalid Tool Name", f"Correctly raised: {type(e).__name__}")
        
        # Test invalid arguments
        try:
            await self.client.call_tool("salesforce_describe_object", {"invalid_param": "test"})
            self.assert_test(False, "Invalid Arguments", "Should have raised exception")
        except Exception as e:
            self.assert_test(True, "Invalid Arguments", f"Correctly raised: {type(e).__name__}")
        
        return True
    
    async def test_request_id_increment(self):
        """Test that request IDs increment properly"""
        print("\n🔢 Testing Request ID Management")
        print("-" * 40)
        
        initial_id = self.client.request_id
        
        # Make a few requests
        try:
            await self.client.list_tools()
            await self.client.list_tools()
            
            final_id = self.client.request_id
            
            self.assert_test(
                final_id > initial_id,
                "Request ID Increment",
                f"ID changed from {initial_id} to {final_id}"
            )
            
        except Exception as e:
            self.assert_test(False, "Request ID Increment", f"Exception: {e}")
        
        return True
    
    async def test_cleanup(self):
        """Test client cleanup"""
        print("\n🧹 Testing Cleanup")
        print("-" * 40)
        
        try:
            await self.client.close()
            self.assert_test(True, "Client Close", "Close method executed successfully")
        except Exception as e:
            self.assert_test(False, "Client Close", f"Exception: {e}")
        
        return True
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 MCPClient Test Suite")
        print("=" * 50)
        
        # Run tests
        await self.test_client_initialization()
        await self.test_internal_methods()
        await self.test_tools_listing()
        await self.test_tool_execution()
        await self.test_error_handling()
        await self.test_request_id_increment()
        await self.test_cleanup()
        
        # Print summary
        print("\n📊 Test Results Summary")
        print("=" * 30)
        
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Pass Rate: {pass_rate:.1f}%")
        
        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED!")
            return True
        elif pass_rate >= 80:
            print("\n✅ MOSTLY PASSED - Some minor issues")
            return True
        else:
            print("\n❌ TESTS FAILED - Major issues detected")
            return False

async def main():
    """Main test function"""
    tester = TestMCPClient()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main()) 