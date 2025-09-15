"""
Dynamic tool registry for Salesforce MCP tools
"""

import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re

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
    """Enhanced information about a single MCP tool"""
    name: str
    description: str
    category: ToolCategory
    input_schema: Dict[str, Any]
    required_params: List[str]
    optional_params: List[str]
    complexity_level: str
    keywords: List[str]
    examples: List[str] = None      # Extracted examples
    rules: List[str] = None         # Extracted rules/notes
    
    def __post_init__(self):
        if self.examples is None:
            self.examples = []
        if self.rules is None:
            self.rules = []

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
        """Build structured registry from raw MCP tools with enhanced info extraction"""
        registry = {}
        
        for tool in raw_tools:
            try:
                name = tool.get("name", "")
                description = tool.get("description", "")
                input_schema = tool.get("inputSchema", {})
                
                # Extract parameters with enhanced details
                properties = input_schema.get("properties", {})
                required = input_schema.get("required", [])
                optional = [k for k in properties.keys() if k not in required]
                
                # Extract examples from description (if any)
                examples = self._extract_examples_from_description(description)
                
                # Extract key rules/notes from description
                rules = self._extract_rules_from_description(description)
                
                # Determine category
                category = self.category_mapping.get(name, ToolCategory.DATA_OPERATIONS)
                
                # Extract keywords from description (enhanced)
                keywords = self._extract_enhanced_keywords(description)
                
                # Determine complexity based on description content
                complexity = self._determine_complexity_from_description(name, description, input_schema)
                
                tool_info = ToolInfo(
                    name=name,
                    description=description,
                    category=category,
                    input_schema=input_schema,
                    required_params=required,
                    optional_params=optional,
                    complexity_level=complexity,
                    keywords=keywords,
                    examples=examples,  # Add examples
                    rules=rules        # Add extracted rules
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
    
    def _extract_examples_from_description(self, description: str) -> List[str]:
        """Extract examples from tool description"""
        examples = []
        
        # Look for "Examples:" or "Example:" sections
        import re
        
        # Pattern to find examples sections
        example_patterns = [
            r"Examples?:\s*\n(.*?)(?=\n\n|\nNotes?:|\nImportant|\Z)",
            r"Examples?:\s*(.*?)(?=\n\n|\nNotes?:|\nImportant|\Z)"
        ]
        
        for pattern in example_patterns:
            matches = re.findall(pattern, description, re.DOTALL | re.IGNORECASE)
            for match in matches:
                # Split by numbered examples
                example_items = re.split(r'\n\s*\d+\.', match)
                for item in example_items:
                    if item.strip():
                        examples.append(item.strip())
        
        return examples[:5]  # Limit to 5 examples
    
    def _extract_rules_from_description(self, description: str) -> List[str]:
        """Extract important rules/notes from tool description"""
        rules = []
        
        import re
        
        # Look for "Notes:", "Important:", "Rules:" sections
        rule_patterns = [
            r"Notes?:\s*\n(.*?)(?=\n\n|\Z)",
            r"Important[^:]*:\s*\n(.*?)(?=\n\n|\Z)",
            r"Rules?:\s*\n(.*?)(?=\n\n|\Z)"
        ]
        
        for pattern in rule_patterns:
            matches = re.findall(pattern, description, re.DOTALL | re.IGNORECASE)
            for match in matches:
                # Split by bullet points or dashes
                rule_items = re.split(r'\n\s*[-•*]', match)
                for item in rule_items:
                    if item.strip():
                        rules.append(item.strip())
        
        return rules[:10]  # Limit to 10 rules
    
    def _extract_enhanced_keywords(self, description: str) -> List[str]:
        """Enhanced keyword extraction from description"""
        keywords = []
        
        # Convert to lowercase for analysis
        desc_lower = description.lower()
        
        # Action words (more comprehensive)
        actions = [
            "query", "search", "describe", "create", "update", "delete", "manage", 
            "read", "write", "execute", "insert", "upsert", "retrieve", "find",
            "list", "get", "show", "analyze", "count", "sum", "average", "group"
        ]
        
        # Salesforce entities (more comprehensive)  
        entities = [
            "account", "contact", "opportunity", "case", "lead", "user", "object", 
            "field", "apex", "trigger", "soql", "sosl", "record", "data",
            "permission", "debug", "log", "metadata", "relationship"
        ]
        
        # Extract action keywords
        for action in actions:
            if action in desc_lower:
                keywords.append(action)
        
        # Extract entity keywords
        for entity in entities:
            if entity in desc_lower:
                keywords.append(entity)
        
        # Extract quoted examples (common patterns)
        import re
        quoted_examples = re.findall(r"'([^']+)'", description)
        keywords.extend([ex.lower() for ex in quoted_examples[:5]])
        
        return list(set(keywords))  # Remove duplicates
    
    def _determine_complexity_from_description(self, name: str, description: str, schema: Dict[str, Any]) -> str:
        """Determine complexity based on description content"""
        desc_lower = description.lower()
        
        # Advanced complexity indicators
        advanced_indicators = [
            "group by", "aggregate", "having", "complex", "advanced", "metadata",
            "permissions", "deploy", "manage", "create object", "apex", "trigger"
        ]
        
        # Complex indicators
        complex_indicators = [
            "relationship", "join", "subquery", "nested", "multiple", "bulk"
        ]
        
        # Simple indicators
        simple_indicators = [
            "simple", "basic", "single", "get", "list", "show"
        ]
        
        # Count indicators
        advanced_count = sum(1 for indicator in advanced_indicators if indicator in desc_lower)
        complex_count = sum(1 for indicator in complex_indicators if indicator in desc_lower)
        simple_count = sum(1 for indicator in simple_indicators if indicator in desc_lower)
        
        # Determine based on counts and required parameters
        required_params = len(schema.get("required", []))
        
        if advanced_count > 0 or required_params > 4:
            return "advanced"
        elif complex_count > 0 or required_params > 2:
            return "complex"
        elif simple_count > 0 or required_params <= 1:
            return "simple"
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