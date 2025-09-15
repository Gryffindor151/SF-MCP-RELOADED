"""
Groq LLM client using LangChain
"""

import logging
from typing import Dict, List, Any, Optional
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage

from ..core.config import config
from ..core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

class GroqLLMClient:
    """LLM client using Groq via LangChain"""
    
    def __init__(self):
        # Validate configuration
        errors = config.validate_llm_config()
        if errors:
            raise ConfigurationError(f"LLM configuration errors: {', '.join(errors)}")
        
        # Initialize Groq client
        self.llm = ChatGroq(
            groq_api_key=config.GROQ_API_KEY,
            model_name=config.GROQ_MODEL,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=config.LLM_MAX_TOKENS,
            timeout=config.LLM_TIMEOUT
        )
        
        logger.info(f"Initialized Groq LLM with model: {config.GROQ_MODEL}")
    
    async def analyze_query(self, user_query: str, available_tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze user query and select appropriate tool with parameters"""
        
        system_prompt = self._build_system_prompt(available_tools)
        user_prompt = self._build_user_prompt(user_query)
        print(f"System prompt: {system_prompt}")
        print(f"User prompt: {user_prompt}")
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            logger.debug(f"Sending query to LLM: {user_query}")
            response = await self.llm.ainvoke(messages)
            
            # Parse LLM response
            result = self._parse_llm_response(response.content)
            
            logger.info(f"LLM selected tool: {result.get('tool_name', 'None')}")
            return result
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            raise
    
    def _build_system_prompt(self, available_tools: List[Dict[str, Any]]) -> str:
        """Build system prompt using rich MCP tool descriptions"""
        
        tools_section = ""
        for i, tool in enumerate(available_tools, 1):
            name = tool.get("name", "")
            description = tool.get("description", "")
            schema = tool.get("inputSchema", {})
            
            # Extract schema details
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            
            # Format parameters from schema
            params_section = ""
            for param, details in properties.items():
                param_type = details.get("type", "string")
                param_desc = details.get("description", "")
                is_required = "REQUIRED" if param in required else "OPTIONAL"
                
                # Handle array types
                if param_type == "array":
                    items = details.get("items", {})
                    if items.get("type"):
                        param_type = f"array of {items['type']}"
                
                params_section += f"    • {param} ({param_type}) [{is_required}]: {param_desc}\n"
            
            tools_section += f"""
{i}. TOOL: {name}

DESCRIPTION:
{description}

PARAMETERS:
{params_section}
"""
        
        return f"""You are a Salesforce expert. Analyze the user's query and select the most appropriate tool from the available options below.

AVAILABLE TOOLS:
{tools_section}

INSTRUCTIONS:
1. Read the user's query carefully
2. Match the query intent with the tool descriptions and examples provided above
3. Select the most appropriate tool based on the detailed descriptions
4. Extract parameters following the parameter descriptions and rules from the tool documentation
5. Use the examples and notes provided in each tool's description as guidance

RESPONSE FORMAT:
Return your analysis as valid JSON:

{{
    "tool_name": "selected_tool_name",
    "parameters": {{
        "param1": "value1",
        "param2": "value2"
    }},
    "reasoning": "Brief explanation referencing the tool description",
    "confidence": 0.95
}}

PARAMETER EXTRACTION RULES:
- Add the required parameters to the parameters object based on the tool description
- Follow the parameter descriptions exactly as provided in each tool's documentation
- Pay attention to the examples and notes in the tool descriptions
- Use the format and constraints specified in each parameter's description 
- For SOQL queries, follow the examples provided in the salesforce_query_records description
- For relationship queries, use the patterns shown in the tool documentation

Select the tool that best matches the user's intent based on the comprehensive descriptions provided above."""

    def _build_user_prompt(self, user_query: str) -> str:
        """Build focused user prompt"""
        return f"""Analyze this Salesforce query and select the appropriate tool:

USER QUERY: "{user_query}"

Based on the detailed tool descriptions provided in the system prompt, select the most appropriate tool and extract the necessary parameters. Use the examples and guidelines from the tool descriptions to ensure correct parameter formatting."""
    
    def _parse_llm_response(self, response_content: str) -> Dict[str, Any]:
        """Parse LLM response and extract structured data"""
        try:
            import json
            import re
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                
                # Validate required fields
                if "tool_name" not in result:
                    raise ValueError("Missing tool_name in LLM response")
                
                return {
                    "tool_name": result.get("tool_name"),
                    "parameters": result.get("parameters", {}),
                    "reasoning": result.get("reasoning", "No reasoning provided"),
                    "confidence": result.get("confidence", 0.5)
                }
            else:
                # Fallback parsing if no JSON found
                logger.warning("No JSON found in LLM response, using fallback parsing")
                return {
                    "tool_name": None,
                    "parameters": {},
                    "reasoning": "Failed to parse LLM response",
                    "confidence": 0.0
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            return {
                "tool_name": None,
                "parameters": {},
                "reasoning": f"JSON parsing error: {e}",
                "confidence": 0.0
            }
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return {
                "tool_name": None,
                "parameters": {},
                "reasoning": f"Parsing error: {e}",
                "confidence": 0.0
            }
    
    async def format_response(self, tool_result: Dict[str, Any], original_query: str, 
                            tool_name: str) -> str:
        """Format tool result into natural language response with error handling"""
        
        # Handle errors first
        if "error" in tool_result or not tool_result:
            error_msg = tool_result.get("error", "Unknown error occurred")
            
            # Provide helpful error explanations
            if "unexpected token" in str(error_msg):
                return f"I encountered a query syntax error. This usually happens when field names are missing or incorrect. Let me know what specific information you're looking for and I'll try again."
            elif "Invalid field" in str(error_msg):
                return f"I tried to access a field that doesn't exist on this object. Could you clarify which fields you're interested in?"
            else:
                return f"I encountered an error while processing your request: {error_msg}. Could you try rephrasing your question?"
        
        system_prompt = """You are a helpful Salesforce assistant. Format the tool execution result into a clear, natural language response.

Guidelines:
- Be conversational and helpful
- Explain the results clearly
- If there are many results, provide a good summary
- Always relate back to the user's original question
- If there are no results, explain what that means"""
        
        user_prompt = f"""Original user query: "{original_query}"
Tool used: {tool_name}
Tool result: {tool_result}

Please format this into a natural, helpful response for the user."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Failed to format response: {e}")
            return f"I got results from Salesforce but had trouble formatting the response. Here's what I found: {tool_result}"