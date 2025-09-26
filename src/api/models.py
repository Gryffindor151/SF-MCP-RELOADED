"""
Simple API models without external dependencies
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

class QueryRequest:
    """Request model for natural language queries"""
    
    def __init__(self, query: str, user_id: Optional[str] = None):
        self.query = query
        self.user_id = user_id
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            query=data.get("query", ""),
            user_id=data.get("user_id")
        )

class QueryResponse:
    """Response model for query results"""
    
    def __init__(self, success: bool, natural_response: str, query: str, 
                 tool_used: Optional[str] = None, error: Optional[str] = None,
                 processing_time_ms: Optional[float] = None):
        self.success = success
        self.natural_response = natural_response
        self.query = query
        self.tool_used = tool_used
        self.error = error
        self.processing_time_ms = processing_time_ms
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> dict:
        result = {
            "success": self.success,
            "natural_response": self.natural_response,
            "query": self.query,
            "timestamp": self.timestamp
        }
        
        if self.tool_used:
            result["tool_used"] = self.tool_used
        
        if self.error:
            result["error"] = self.error
            
        if self.processing_time_ms is not None:
            result["processing_time_ms"] = self.processing_time_ms
        
        return result 