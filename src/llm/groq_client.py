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
        """Build system prompt with available tools"""
        
        tools_description = ""
        for tool in available_tools:
            name = tool.get("name", "")
            description = tool.get("description", "")
            schema = tool.get("inputSchema", {})
            required = schema.get("required", [])
            
            tools_description += f"""
Tool: {name}
Description: {description}
Required Parameters: {required}
"""
        
        return f"""You are a Salesforce expert assistant. Your job is to analyze user queries and select the most appropriate Salesforce tool to fulfill the request.

Available Tools:
{tools_description}

Instructions:
1. Analyze the user's query to understand their intent
2. Select the most appropriate tool from the available options
3. Extract the required parameters from the query
4. Return your response in this JSON format:

{{
    "tool_name": "selected_tool_name",
    "parameters": {{
        "param1": "value1",
        "param2": "value2"
    }},
    "reasoning": "Brief explanation of why this tool was chosen",
    "confidence": 0.95
}}

Guidelines:
- For queries asking to "show", "get", "find" records: Use salesforce_query_records
- For counting or aggregation: Use salesforce_aggregate_query
- For object information: Use salesforce_describe_object
- For searching objects: Use salesforce_search_objects
- For data modifications: Use salesforce_dml_records

Always extract parameters carefully and provide reasoning for your choice."""
    
    def _build_user_prompt(self, user_query: str) -> str:
        """Build user prompt with the specific query"""
        return f"""Please analyze this Salesforce query and select the appropriate tool:

User Query: "{user_query}"

Analyze the query and provide your tool selection and parameter extraction in the specified JSON format."""
    
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
        """Format tool result into natural language response"""
        
        system_prompt = """You are a helpful Salesforce assistant. Format the tool execution result into a clear, natural language response for the user.

Guidelines:
- Be conversational and helpful
- Explain the results clearly
- If there are errors, explain them in simple terms
- If there are many results, summarize them appropriately
- Always relate back to the user's original question"""
        
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
            return f"I got results from Salesforce, but had trouble formatting the response. Raw result: {tool_result}" 