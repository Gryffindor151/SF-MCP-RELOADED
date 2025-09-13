"""
MCP tool definitions and schemas
"""

# Available Salesforce MCP tools
SALESFORCE_TOOLS = {
    "salesforce_search_objects": {
        "description": "Search for Salesforce objects by name pattern",
        "parameters": ["searchPattern"]
    },
    "salesforce_describe_object": {
        "description": "Get detailed schema of a Salesforce object",
        "parameters": ["objectName"]
    },
    "salesforce_query_records": {
        "description": "Query records from Salesforce using SOQL",
        "parameters": ["objectName", "fields", "whereClause", "orderBy", "limit"]
    },
    "salesforce_aggregate_query": {
        "description": "Execute aggregate queries with GROUP BY",
        "parameters": ["objectName", "selectFields", "groupByFields", "whereClause", "havingClause"]
    },
    "salesforce_dml_records": {
        "description": "Insert, update, delete, or upsert records",
        "parameters": ["operation", "objectName", "records"]
    },
    "salesforce_search_all": {
        "description": "Search across multiple objects using SOSL",
        "parameters": ["searchTerm", "objects"]
    }
}

def get_tool_description(tool_name: str) -> str:
    """Get description for a specific tool"""
    return SALESFORCE_TOOLS.get(tool_name, {}).get("description", "")

def get_tool_parameters(tool_name: str) -> list:
    """Get parameters for a specific tool"""
    return SALESFORCE_TOOLS.get(tool_name, {}).get("parameters", []) 