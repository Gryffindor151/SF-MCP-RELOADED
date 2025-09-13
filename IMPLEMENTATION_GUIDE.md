# Implementation Guide

## Phase 1: MCP Integration

### Dependencies to add:
```bash
pip install httpx asyncio-subprocess
```

### Files to implement:
- `src/mcp/client.py` - MCP client wrapper
- `scripts/test_phase1.py` - Phase 1 testing

### Goals:
- Connect to Salesforce MCP server
- List available tools
- Test basic tool calls

## Phase 2: LLM Integration

### Dependencies to add:
```bash
pip install langchain langchain-groq
```

### Files to implement:
- `src/llm/groq_client.py` - Groq LLM integration
- `src/llm/prompts.py` - LangChain prompts
- `scripts/test_phase2.py` - Phase 2 testing

### Goals:
- Natural language query analysis
- Tool selection and parameter extraction
- Response formatting

## Phase 3: FastAPI HTTP API

### Dependencies to add:
```bash
pip install fastapi uvicorn
```

### Files to implement:
- `src/api/main.py` - FastAPI application
- `src/api/models.py` - Request/Response models (without Pydantic)
- `src/api/routes.py` - API routes
- `scripts/test_phase3.py` - Phase 3 testing

### Goals:
- REST API endpoints
- Request/response handling
- Error management

## Phase 4: Testing & Optimization

### Dependencies to add:
```bash
pip install pytest pytest-asyncio
```

### Files to implement:
- `tests/test_mcp.py` - MCP tests
- `tests/test_llm.py` - LLM tests  
- `tests/test_api.py` - API tests
- `scripts/test_full_integration.py` - Full integration test

### Goals:
- Comprehensive testing
- Performance optimization
- Documentation

## Getting Started

1. Run setup:
```bash
python setup_project.py
```

2. Validate setup:
```bash
python scripts/validate_setup.py
```

3. Update `.env` with your credentials

4. Start with Phase 1 implementation 