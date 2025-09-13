"""
Dynamic tool registry for Salesforce MCP tools
"""

import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ToolCategory(Enum):
    """Tool categories based on functionality"""
    DATA_OPERATIONS = "data_operations"
    SCHEMA_MANAGEMENT = "schema_management"
    OBJECT_DISCOVERY = "object_discovery"
    CODE_MANAGEMENT = "code_management"
    DEBUGGING = "debugging"

@dataclass
class ToolInfo:
    """Information about a single MCP tool"""
    name: str
    description: str
    category: ToolCategory
    input_schema: Dict[str, Any]
    required_params: List[str]
    optional_params: List[str]
    complexity_level: str
    keywords: List[str]

class ToolRegistry:
    """Dynamic registry for MCP tools with categorization and caching"""
    
    def __init__(self, mcp_client, cache_ttl: int = 300):
        self.mcp_client = mcp_client
        self.cache_ttl = cache_ttl  # 5 minutes default
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        self._registry_cache: Optional[Dict[str, ToolInfo]] = None
        self._categories_cache: Optional[Dict[ToolCategory, List[str]]] = None
        self._last_update = 0
        
        # Category mapping based on tool names
        self.category_mapping = {
            # Data Operations
            "salesforce_query_records": ToolCategory.DATA_OPERATIONS,
            "salesforce_aggregate_query": ToolCategory.DATA_OPERATIONS,
            "salesforce_dml_records": ToolCategory.DATA_OPERATIONS,
            "salesforce_search_all": ToolCategory.DATA_OPERATIONS,
            
            # Schema Management
            "salesforce_describe_object": ToolCategory.SCHEMA_MANAGEMENT,
            "salesforce_manage_object": ToolCategory.SCHEMA_MANAGEMENT,
            "salesforce_manage_field": ToolCategory.SCHEMA_MANAGEMENT,
            "salesforce_manage_field_permissions": ToolCategory.SCHEMA_MANAGEMENT,
            
            # Object Discovery
            "salesforce_search_objects": ToolCategory.OBJECT_DISCOVERY,
            
            # Code Management
            "salesforce_read_apex": ToolCategory.CODE_MANAGEMENT,
            "salesforce_write_apex": ToolCategory.CODE_MANAGEMENT,
            "salesforce_read_apex_trigger": ToolCategory.CODE_MANAGEMENT,
            "salesforce_write_apex_trigger": ToolCategory.CODE_MANAGEMENT,
            "salesforce_execute_anonymous": ToolCategory.CODE_MANAGEMENT,
            
            # Debugging
            "salesforce_manage_debug_logs": ToolCategory.DEBUGGING,
        }
    
    async def refresh_tools(self, force: bool = False) -> bool:
        """Refresh tools from MCP server"""
        current_time = time.time()
        
        if not force and self._tools_cache and (current_time - self._last_update) < self.cache_ttl:
            logger.debug("Using cached tools")
            return True
        
        try:
            logger.info("Refreshing tools from MCP server...")
            raw_tools = await self.mcp_client.list_tools()
            
            if not raw_tools:
                logger.warning("No tools received from MCP server")
                return False
            
            self._tools_cache = raw_tools
            self._registry_cache = self._build_registry(raw_tools)
            self._categories_cache = self._build_categories()
            self._last_update = current_time
            
            logger.info(f"Successfully refreshed {len(raw_tools)} tools")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh tools: {e}")
            return False
    
    def _build_registry(self, raw_tools: List[Dict[str, Any]]) -> Dict[str, ToolInfo]:
        """Build structured registry from raw MCP tools"""
        registry = {}
        
        for tool in raw_tools:
            try:
                name = tool.get("name", "")
                description = tool.get("description", "")
                input_schema = tool.get("inputSchema", {})
                
                # Extract parameters
                properties = input_schema.get("properties", {})
                required = input_schema.get("required", [])
                optional = [k for k in properties.keys() if k not in required]
                
                # Determine category
                category = self.category_mapping.get(name, ToolCategory.DATA_OPERATIONS)
                
                # Extract keywords from description
                keywords = self._extract_keywords(description)
                
                # Determine complexity
                complexity = self._determine_complexity(name, input_schema, description)
                
                tool_info = ToolInfo(
                    name=name,
                    description=description,
                    category=category,
                    input_schema=input_schema,
                    required_params=required,
                    optional_params=optional,
                    complexity_level=complexity,
                    keywords=keywords
                )
                
                registry[name] = tool_info
                
            except Exception as e:
                logger.warning(f"Failed to process tool {tool.get('name', 'unknown')}: {e}")
        
        return registry
    
    def _build_categories(self) -> Dict[ToolCategory, List[str]]:
        """Build category to tool names mapping"""
        categories = {category: [] for category in ToolCategory}
        
        if self._registry_cache:
            for tool_name, tool_info in self._registry_cache.items():
                categories[tool_info.category].append(tool_name)
        
        return categories
    
    def _extract_keywords(self, description: str) -> List[str]:
        """Extract relevant keywords from tool description"""
        # Simple keyword extraction - can be enhanced with NLP
        keywords = []
        
        # Common action words
        actions = ["query", "search", "describe", "create", "update", "delete", "manage", "read", "write", "execute"]
        for action in actions:
            if action.lower() in description.lower():
                keywords.append(action)
        
        # Salesforce entities
        entities = ["account", "contact", "opportunity", "case", "lead", "object", "field", "apex", "trigger"]
        for entity in entities:
            if entity.lower() in description.lower():
                keywords.append(entity)
        
        return keywords
    
    def _determine_complexity(self, name: str, schema: Dict[str, Any], description: str) -> str:
        """Determine tool complexity level"""
        required_params = len(schema.get("required", []))
        total_params = len(schema.get("properties", {}))
        
        # Simple heuristics
        if "aggregate" in name or "complex" in description.lower():
            return "complex"
        elif required_params <= 1 and total_params <= 3:
            return "simple"
        elif "manage" in name or "write" in name or "create" in name:
            return "advanced"
        else:
            return "moderate"
    
    async def get_all_tools(self) -> Dict[str, ToolInfo]:
        """Get all tools in registry"""
        await self.refresh_tools()
        return self._registry_cache or {}
    
    async def get_tools_by_category(self, category: ToolCategory) -> List[ToolInfo]:
        """Get tools filtered by category"""
        await self.refresh_tools()
        
        if not self._registry_cache:
            return []
        
        return [
            tool_info for tool_info in self._registry_cache.values()
            if tool_info.category == category
        ]
    
    async def get_tool_info(self, tool_name: str) -> Optional[ToolInfo]:
        """Get information about a specific tool"""
        await self.refresh_tools()
        
        if not self._registry_cache:
            return None
        
        return self._registry_cache.get(tool_name)
    
    async def search_tools(self, keywords: List[str], categories: List[ToolCategory] = None) -> List[ToolInfo]:
        """Search tools by keywords and optional categories"""
        await self.refresh_tools()
        
        if not self._registry_cache:
            return []
        
        results = []
        keywords_lower = [k.lower() for k in keywords]
        
        for tool_info in self._registry_cache.values():
            # Category filter
            if categories and tool_info.category not in categories:
                continue
            
            # Keyword matching
            tool_text = f"{tool_info.name} {tool_info.description} {' '.join(tool_info.keywords)}".lower()
            
            score = 0
            for keyword in keywords_lower:
                if keyword in tool_text:
                    score += 1
            
            if score > 0:
                results.append((tool_info, score))
        
        # Sort by relevance score
        results.sort(key=lambda x: x[1], reverse=True)
        return [tool_info for tool_info, _ in results]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        if not self._registry_cache or not self._categories_cache:
            return {"error": "Registry not initialized"}
        
        return {
            "total_tools": len(self._registry_cache),
            "categories": {
                category.value: len(tools) 
                for category, tools in self._categories_cache.items()
            },
            "last_update": self._last_update,
            "cache_age": time.time() - self._last_update
        } 