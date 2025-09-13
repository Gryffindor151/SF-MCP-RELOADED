"""
Custom exceptions for the application
"""

class SalesforceAPIError(Exception):
    """Raised when Salesforce API operations fail"""
    pass

class MCPConnectionError(Exception):
    """Raised when MCP server connection fails"""
    pass

class ConfigurationError(Exception):
    """Raised when configuration is invalid"""
    pass 