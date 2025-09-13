"""
Tool selector that combines category classification and LLM analysis
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

from .tool_registry import ToolRegistry, ToolCategory, ToolInfo
from .category_classifier import CategoryClassifier, IntentAnalysis
from .groq_client import GroqLLMClient

logger = logging.getLogger(__name__)

class ToolSelector:
    """Selects appropriate tools based on user queries"""
    
    def __init__(self, mcp_client):
        self.tool_registry = ToolRegistry(mcp_client)
        self.category_classifier = CategoryClassifier()
        self.llm_client = GroqLLMClient()
    
    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """Complete query processing: selection → execution → natural response"""
        
        try:
            # Step 1: Select tool and extract parameters
            logger.info("Processing user query...")
            tool_selection = await self.select_tool(user_query)
            
            if not tool_selection.get("success"):
                return {
                    "success": False,
                    "natural_response": "I couldn't understand your query. Could you please rephrase it?",
                    "error": tool_selection.get("error")
                }
            
            # Step 2: Execute the selected tool
            tool_name = tool_selection["tool_name"]
            parameters = tool_selection["parameters"]
            
            logger.info(f"Executing tool: {tool_name}")
            
            # Get MCP client from tool registry
            tool_result = await self.tool_registry.mcp_client.call_tool(tool_name, parameters)
            
            # Step 3: Format result into natural language
            logger.info("Formatting response...")
            natural_response = await self.llm_client.format_response(
                tool_result, user_query, tool_name
            )
            
            return {
                "success": True,
                "natural_response": natural_response,
                "tool_used": tool_name,
                "parameters_used": parameters,
                "raw_result": tool_result,
                "metadata": {
                    "confidence": tool_selection.get("confidence", 0.5),
                    "reasoning": tool_selection.get("reasoning", ""),
                    "category": tool_selection.get("selected_tool_info", {}).get("category", "")
                }
            }
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            
            # Return user-friendly error message
            error_response = self._get_friendly_error_message(str(e))
            
            return {
                "success": False,
                "natural_response": error_response,
                "error": str(e)
            }
    
    def _get_friendly_error_message(self, error: str) -> str:
        """Convert technical errors to user-friendly messages"""
        
        error_lower = error.lower()
        
        if "unexpected token" in error_lower or "soql" in error_lower:
            return "I had trouble building the query. Could you be more specific about what information you're looking for?"
        
        elif "invalid field" in error_lower:
            return "I tried to access a field that doesn't exist. Could you clarify which specific information you need?"
        
        elif "timeout" in error_lower:
            return "The request took too long to process. Please try again or simplify your query."
        
        elif "permission" in error_lower or "access" in error_lower:
            return "You don't have permission to access this information. Please check with your Salesforce administrator."
        
        elif "connection" in error_lower or "network" in error_lower:
            return "I'm having trouble connecting to Salesforce. Please try again in a moment."
        
        else:
            return "I encountered an issue while processing your request. Please try rephrasing your question or contact support if the problem persists."

    async def select_tool(self, user_query: str) -> Dict[str, Any]:
        """Select the best tool for the user query"""
        
        try:
            # Step 1: Analyze query intent and classify categories
            logger.info("Analyzing query intent...")
            intent_analysis = self.category_classifier.analyze_query(user_query)
            
            # Step 2: Get ranked categories
            ranked_categories = self.category_classifier.get_ranked_categories(
                intent_analysis, min_score=0.1
            )
            
            if not ranked_categories:
                logger.warning("No suitable categories found")
                return self._create_error_result("Could not determine query intent")
            
            # Step 3: Get tools from top categories
            logger.info(f"Top category: {ranked_categories[0][0].value}")
            candidate_tools = await self._get_candidate_tools(ranked_categories[:2])  # Top 2 categories
            
            if not candidate_tools:
                logger.warning("No candidate tools found")
                return self._create_error_result("No suitable tools found")
            
            # Step 4: Use LLM to select best tool and extract parameters
            logger.info("Using LLM for final tool selection...")
            llm_result = await self.llm_client.analyze_query(user_query, candidate_tools)
            
            # Step 5: Validate and enhance result
            validated_result = await self._validate_tool_selection(llm_result, candidate_tools)
            
            # Add analysis metadata
            validated_result.update({
                "intent_analysis": {
                    "primary_intent": intent_analysis.primary_intent,
                    "confidence": intent_analysis.confidence,
                    "entities": intent_analysis.entities,
                    "action_words": intent_analysis.action_words
                },
                "category_ranking": [(cat.value, score) for cat, score in ranked_categories]
            })
            
            return validated_result
            
        except Exception as e:
            logger.error(f"Tool selection failed: {e}")
            return self._create_error_result(f"Tool selection error: {e}")
    
    async def _get_candidate_tools(self, ranked_categories: List[Tuple[ToolCategory, float]]) -> List[Dict[str, Any]]:
        """Get candidate tools from ranked categories"""
        candidate_tools = []
        
        for category, score in ranked_categories:
            tools = await self.tool_registry.get_tools_by_category(category)
            
            for tool_info in tools:
                candidate_tools.append({
                    "name": tool_info.name,
                    "description": tool_info.description,
                    "inputSchema": tool_info.input_schema,
                    "category": category.value,
                    "category_score": score,
                    "complexity": tool_info.complexity_level,
                    "keywords": tool_info.keywords
                })
        
        # Remove duplicates and sort by category score
        seen_tools = set()
        unique_tools = []
        
        for tool in sorted(candidate_tools, key=lambda x: x["category_score"], reverse=True):
            if tool["name"] not in seen_tools:
                unique_tools.append(tool)
                seen_tools.add(tool["name"])
        
        logger.info(f"Found {len(unique_tools)} candidate tools")
        return unique_tools
    
    async def _validate_tool_selection(self, llm_result: Dict[str, Any], 
                                     candidate_tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate and enhance LLM tool selection"""
        
        tool_name = llm_result.get("tool_name")
        parameters = llm_result.get("parameters", {})
        
        # Check if selected tool exists in candidates
        selected_tool = None
        for tool in candidate_tools:
            if tool["name"] == tool_name:
                selected_tool = tool
                break
        
        if not selected_tool:
            logger.warning(f"LLM selected invalid tool: {tool_name}")
            # Fallback to first candidate tool
            if candidate_tools:
                selected_tool = candidate_tools[0]
                tool_name = selected_tool["name"]
                logger.info(f"Falling back to: {tool_name}")
            else:
                return self._create_error_result("No valid tools available")
        
        # Validate parameters against schema
        validated_params = self._validate_parameters(parameters, selected_tool["inputSchema"])
        
        return {
            "success": True,
            "tool_name": tool_name,
            "parameters": validated_params,
            "reasoning": llm_result.get("reasoning", ""),
            "confidence": llm_result.get("confidence", 0.5),
            "selected_tool_info": {
                "category": selected_tool["category"],
                "complexity": selected_tool["complexity"],
                "description": selected_tool["description"]
            }
        }
    
    def _validate_parameters(self, parameters: Dict[str, Any], 
                           input_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and auto-correct parameters against tool schema"""
        
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        validated = {}
        
        # Check required parameters
        for req_param in required:
            if req_param in parameters:
                validated[req_param] = parameters[req_param]
            else:
                logger.warning(f"Missing required parameter: {req_param}")
                # Auto-add defaults for common parameters
                default_value = self._get_default_parameter_value(req_param, parameters)
                if default_value is not None:
                    validated[req_param] = default_value
                    logger.info(f"Auto-added default for {req_param}: {default_value}")
        
        # Add optional parameters that were provided
        for param, value in parameters.items():
            if param in properties and param not in validated:
                # Auto-correct common issues
                corrected_value = self._auto_correct_parameter(param, value, properties[param])
                validated[param] = corrected_value
        
        return validated

    def _get_default_parameter_value(self, param_name: str, existing_params: Dict[str, Any]) -> Any:
        """Get sensible defaults for missing required parameters"""
        
        defaults = {
            # Common field defaults based on object type
            "fields": self._get_default_fields(existing_params.get("objectName", "")),
            "objectName": "Account",  # Default to Account if not specified
            "searchPattern": "Account"  # Default search pattern
        }
        
        return defaults.get(param_name)

    def _get_default_fields(self, object_name: str) -> List[str]:
        """Get default fields for common Salesforce objects"""
        
        field_defaults = {
            "Account": ["Id", "Name", "Industry", "Type", "Phone", "Website"],
            "Contact": ["Id", "FirstName", "LastName", "Email", "Phone", "AccountId"],
            "Opportunity": ["Id", "Name", "StageName", "Amount", "CloseDate", "AccountId"],
            "Case": ["Id", "Subject", "Status", "Priority", "AccountId", "ContactId"],
            "Lead": ["Id", "FirstName", "LastName", "Email", "Company", "Status"]
        }
        
        return field_defaults.get(object_name, ["Id", "Name"])

    def _auto_correct_parameter(self, param_name: str, value: Any, param_schema: Dict[str, Any]) -> Any:
        """Auto-correct common parameter issues"""
        
        if param_name == "whereClause" and isinstance(value, str):
            # Auto-quote string values in WHERE clauses
            value = self._fix_where_clause_quotes(value)
        
        elif param_name == "fields" and isinstance(value, list):
            # Ensure fields array is not empty
            if not value:
                logger.warning("Empty fields array detected, adding default fields")
                return ["Id", "Name"]
        
        elif param_name == "objectName" and isinstance(value, str):
            # Capitalize first letter of object names
            value = value.capitalize()
        
        return value

    def _fix_where_clause_quotes(self, where_clause: str) -> str:
        """Auto-fix quotes in WHERE clauses"""
        import re
        
        # Pattern to find unquoted string values after = operator
        # Example: Industry = Technology -> Industry = 'Technology'
        pattern = r"(\w+)\s*=\s*([A-Za-z][A-Za-z0-9\s]*?)(?=\s|$|AND|OR)"
        
        def quote_replacement(match):
            field = match.group(1)
            value = match.group(2).strip()
            
            # Don't quote if already quoted or if it's a number
            if (value.startswith("'") and value.endswith("'")) or value.isdigit():
                return f"{field} = {value}"
            else:
                return f"{field} = '{value}'"
        
        corrected = re.sub(pattern, quote_replacement, where_clause)
        logger.info(f"Auto-corrected WHERE clause: {where_clause} -> {corrected}")
        return corrected
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error result"""
        return {
            "success": False,
            "error": error_message,
            "tool_name": None,
            "parameters": {},
            "reasoning": error_message,
            "confidence": 0.0
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get tool selector statistics"""
        registry_stats = self.tool_registry.get_stats()
        
        return {
            "tool_registry": registry_stats,
            "llm_model": self.llm_client.llm.model_name,
            "available_categories": [cat.value for cat in ToolCategory]
        } 