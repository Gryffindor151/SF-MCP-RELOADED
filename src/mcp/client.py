"""
MCP client for communicating with Salesforce MCP Server via shell commands
"""

import json
import subprocess
from typing import Dict, List, Any
import logging

from ..core.config import config
from ..core.exceptions import MCPConnectionError, SalesforceAPIError

logger = logging.getLogger(__name__)

class MCPClient:
    """Client for communicating with Salesforce MCP Server via shell commands."""
    
    def __init__(self):
        self.request_id = 0
        self.timeout = 30
    
    def _get_shell_command(self, json_request: str) -> str:
        """Get shell command with environment variables - matches working bash script."""
        env_vars = config.get_salesforce_env_vars()
        
        env_exports = f"""
export SALESFORCE_CONNECTION_TYPE="{env_vars['SALESFORCE_CONNECTION_TYPE']}"
export SALESFORCE_USERNAME="{env_vars['SALESFORCE_USERNAME']}"
export SALESFORCE_PASSWORD="{env_vars['SALESFORCE_PASSWORD']}"
export SALESFORCE_TOKEN="{env_vars['SALESFORCE_TOKEN']}"
export SALESFORCE_INSTANCE_URL="{env_vars['SALESFORCE_INSTANCE_URL']}"
"""
        
        # Use exact same command as working bash script
        command = f"{env_exports}echo '{json_request}' | npx @tsmztech/mcp-server-salesforce"
        return command
    
    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse MCP server response format."""
        # Check if it's an error response
        if response.get("isError", False):
            error_text = response.get("content", [{}])[0].get("text", "Unknown error")
            raise SalesforceAPIError(f"MCP server error: {error_text}")
        
        # The MCP server returns the correct format directly
        # No special parsing needed for most responses
        return response
    
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a JSON-RPC request to the MCP server."""
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_request_id(),
            "method": method,
            "params": params or {}
        }
        
        json_request = json.dumps(request)
        shell_command = self._get_shell_command(json_request)
        
        logger.info(f"Sending MCP request: {method}")
        logger.debug(f"Shell command: {shell_command}")
        
        try:
            # Execute shell command with fixed timeout
            result = subprocess.run(
                shell_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode != 0:
                error_msg = f"Shell command failed (return code {result.returncode}): {result.stderr}"
                logger.error(error_msg)
                raise MCPConnectionError(error_msg)
            
            response = json.loads(result.stdout.strip())
            
            if "error" in response:
                error_msg = f"MCP server error: {response['error']}"
                logger.error(error_msg)
                raise SalesforceAPIError(error_msg)
            
            # Parse the response format
            return self._parse_response(response.get("result", {}))
            
        except subprocess.TimeoutExpired:
            timeout_msg = f"MCP server request timed out after {self.timeout} seconds"
            logger.error(timeout_msg)
            raise MCPConnectionError(timeout_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse MCP server response: {e}"
            logger.error(error_msg)
            raise MCPConnectionError("Invalid response from MCP server")
        except Exception as e:
            error_msg = f"Error communicating with MCP server: {e}"
            logger.error(error_msg)
            raise MCPConnectionError(error_msg)
    
    def _get_next_request_id(self) -> int:
        """Get next request ID for JSON-RPC."""
        self.request_id += 1
        return self.request_id
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools from MCP server."""
        try:
            result = await self._send_request("tools/list")
            tools = result.get("tools", [])
            logger.info(f"Found {len(tools)} tools")
            return tools
        except Exception as e:
            logger.error(f"Failed to list MCP tools: {e}")
            raise
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool on the MCP server."""
        try:
            logger.info(f"Calling tool: {tool_name} with args: {arguments}")
            
            result = await self._send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })
            
            logger.info(f"Tool {tool_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Failed to call MCP tool {tool_name}: {e}")
            raise
    
    async def start_server(self) -> bool:
        """Start server method for compatibility - not needed with shell approach."""
        # Validate configuration
        errors = config.validate_salesforce_config()
        if errors:
            raise MCPConnectionError(f"Configuration errors: {', '.join(errors)}")
        
        logger.info("MCP Client initialized (shell-based)")
        return True
    
    async def close(self):
        """Close method for compatibility - not needed with shell approach."""
        logger.info("MCP Client closed (shell-based)") 