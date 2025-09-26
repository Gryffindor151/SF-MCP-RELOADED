"""
FastAPI application for Salesforce Natural Language API
"""

import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .models import QueryRequest, QueryResponse
from .auth import verify_token
from ..core.config import config
from ..mcp.client import MCPClient
from ..llm.tool_selector import ToolSelector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
mcp_client: MCPClient = None
tool_selector: ToolSelector = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global mcp_client, tool_selector
    
    # Startup
    logger.info("🚀 Starting Salesforce Natural Language API...")
    
    try:
        # Validate configuration
        sf_errors = config.validate_salesforce_config()
        llm_errors = config.validate_llm_config()
        
        if sf_errors or llm_errors:
            logger.error(f"Configuration errors: {sf_errors + llm_errors}")
            raise Exception(f"Configuration errors: {sf_errors + llm_errors}")
        
        # Initialize MCP client
        mcp_client = MCPClient()
        await mcp_client.start_server()
        logger.info("✅ MCP client initialized")
        
        # Initialize tool selector
        tool_selector = ToolSelector(mcp_client)
        logger.info("✅ Tool selector initialized")
        
        logger.info("🎉 API startup complete!")
        
    except Exception as e:
        logger.error(f"❌ Failed to start API: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down API...")
    if mcp_client:
        await mcp_client.close()
        logger.info("✅ MCP client closed")

# Create FastAPI app
app = FastAPI(
    title="Salesforce Natural Language API",
    description="Natural language interface to Salesforce using MCP and LLM",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    start_time = time.time()
    
    logger.info(f"📥 {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    logger.info(f"📤 {request.method} {request.url.path} - {response.status_code} ({process_time:.2f}ms)")
    
    return response

# Health check endpoint (no auth required)
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    
    components = {
        "mcp_client": "healthy" if mcp_client else "unavailable",
        "tool_selector": "healthy" if tool_selector else "unavailable"
    }
    
    status = "healthy" if all(s == "healthy" for s in components.values()) else "degraded"
    
    return {
        "status": status,
        "version": "1.0.0",
        "components": components
    }

# Main query endpoint
@app.post("/query")
async def process_query(
    request_data: dict,
    current_user: dict = Depends(verify_token)
):
    """Process natural language query"""
    
    start_time = time.time()
    
    try:
        # Parse request
        query_request = QueryRequest.from_dict(request_data)
        
        if not query_request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        logger.info(f"🔍 Processing query: {query_request.query}")
        
        # Process query
        result = await tool_selector.process_query(query_request.query)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Create response
        response = QueryResponse(
            success=result.get("success", False),
            natural_response=result.get("natural_response", "No response generated"),
            query=query_request.query,
            tool_used=result.get("tool_used"),
            error=result.get("error"),
            processing_time_ms=processing_time_ms
        )
        
        logger.info(f"✅ Query processed ({processing_time_ms:.2f}ms)")
        return response.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        logger.error(f"❌ Query processing failed: {e}")
        
        response = QueryResponse(
            success=False,
            natural_response="I encountered an error while processing your request.",
            query=request_data.get("query", ""),
            error=str(e),
            processing_time_ms=processing_time_ms
        )
        
        return response.to_dict()

# Tools information endpoint
@app.get("/tools")
async def get_tools_info(current_user: dict = Depends(verify_token)):
    """Get information about available Salesforce tools"""
    
    try:
        tools = await tool_selector.tool_registry.get_all_tools()
        
        tools_info = []
        for tool_name, tool_info in tools.items():
            tools_info.append({
                "name": tool_info.name,
                "description": tool_info.description[:200] + "..." if len(tool_info.description) > 200 else tool_info.description,
                "category": tool_info.category.value,
                "required_parameters": tool_info.required_params
            })
        
        return {
            "tools": tools_info,
            "total_tools": len(tools_info)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get tools info: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tools information")

# Examples endpoint (no auth required)
@app.get("/examples")
async def get_query_examples():
    """Get example queries"""
    
    return {
        "examples": [
            {
                "category": "Data Queries",
                "queries": [
                    "Show me all Technology accounts",
                    "Find contacts from Microsoft",
                    "Get opportunities closing this month"
                ]
            },
            {
                "category": "Schema Information",
                "queries": [
                    "What fields are available on Contact?",
                    "Describe the Account object",
                    "Show me Opportunity object structure"
                ]
            },
            {
                "category": "Object Discovery",
                "queries": [
                    "Search for objects containing Order",
                    "Find objects with Customer in the name"
                ]
            }
        ]
    }

# Root endpoint
@app.get("/")
async def root():
    """API information endpoint"""
    
    return {
        "name": "Salesforce Natural Language API",
        "version": "1.0.0",
        "description": "Natural language interface to Salesforce using MCP and LLM",
        "endpoints": {
            "POST /query": "Process natural language queries (requires auth)",
            "GET /tools": "Get available Salesforce tools (requires auth)",
            "GET /examples": "Get example queries",
            "GET /health": "Health check",
            "GET /docs": "API documentation"
        }
    } 