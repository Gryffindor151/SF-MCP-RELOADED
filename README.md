# Salesforce Natural Language API

A Python HTTP API that provides a natural language interface to Salesforce using MCP (Model Context Protocol), LangChain, and FastAPI.

## Project Structure

```
SF-MCP-RELOADED/
├── src/
│   ├── __init__.py
│   ├── mcp/           # MCP client and tools
│   ├── llm/           # LangChain + Groq integration
│   ├── api/           # FastAPI application
│   └── core/          # Configuration and utilities
├── tests/             # Test files
├── scripts/           # Phase testing scripts
├── .env.example       # Environment template
├── requirements.txt   # Dependencies
└── README.md
```

## Implementation Phases

### Phase 1: MCP Integration
- MCP client wrapper
- Tool discovery and calling
- Salesforce connection testing

### Phase 2: LLM Integration  
- LangChain with Groq
- Natural language query analysis
- Response formatting

### Phase 3: FastAPI HTTP API
- REST endpoints
- Request/response handling
- Error management

### Phase 4: Testing & Optimization
- Comprehensive testing
- Performance optimization
- Documentation

## Getting Started

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
```

2. Install initial dependencies:
```bash
pip install python-dotenv
```

3. Copy environment template:
```bash
cp .env.example .env
```

4. Update `.env` with your credentials

5. Start with Phase 1 implementation
```

## Step 4: Install Initial Dependencies

Now let's install the basic dependencies:

```bash
# Install python-dotenv for environment management
pip install python-dotenv
```

## Step 5: Create Environment File

Copy the environment template:

```bash
cp .env.example .env
```

Now you need to edit the `.env` file with your actual credentials. You can use any text editor:

```bash
# Using nano
nano .env

# Using vim
vim .env

# Using VS Code
code .env
```

Update the `.env` file with your actual Salesforce and Groq credentials.

## Step 6: Verify Setup

Let's create a simple verification script to check our setup:

```python:scripts/check_setup.py
#!/usr/bin/env python3
"""
Check if the basic project setup is correct
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def check_directories():
    """Check if required directories exist"""
    required_dirs = [
        "src",
        "src/mcp",
        "src/llm", 
        "src/api",
        "src/core",
        "tests",
        "scripts"
    ]
    
    missing = []
    for directory in required_dirs:
        if not Path(directory).exists():
            missing.append(directory)
    
    if missing:
        print(f"❌ Missing directories: {missing}")
        return False
    
    print("✅ All required directories exist")
    return True

def check_files():
    """Check if required files exist"""
    required_files = [
        ".env.example",
        "requirements.txt",
        "README.md"
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print(f"❌ Missing files: {missing}")
        return False
    
    print("✅ All required files exist")
    return True

def check_env():
    """Check if .env file exists and has required variables"""
    if not Path(".env").exists():
        print("❌ .env file not found")
        print("   Run: cp .env.example .env")
        return False
    
    # Load environment variables
    load_dotenv()
    
    required_vars = [
        "SALESFORCE_USERNAME",
        "SALESFORCE_PASSWORD",
        "SALESFORCE_TOKEN",
        "SALESFORCE_INSTANCE_URL",
        "GROQ_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var) == f"your-{var.lower().replace('_', '-')}":
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or placeholder values in .env: {missing_vars}")
        print("   Please update .env with your actual credentials")
        return False
    
    print("✅ Environment configuration is complete")
    return True

def main():
    """Main check function"""
    print("🔍 Checking Project Setup")
    print("=" * 40)
    
    dirs_ok = check_directories()
    files_ok = check_files()
    env_ok = check_env()
    
    if dirs_ok and files_ok and env_ok:
        print("\n✅ Project setup is complete!")
        print("Ready to start Phase 1: MCP Integration")
    else:
        print("\n❌ Setup incomplete")
        print("Please fix the issues above")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

Now let's test our setup:

```bash
python scripts/check_setup.py
```

## Step 7: Create Basic Package Files

Let's create the basic package initialization files:

```python:src/__init__.py
"""
Salesforce Natural Language API Package
"""

__version__ = "1.0.0"
__author__ = "Your Name"
```

```python:src/core/__init__.py
"""
Core utilities and configuration
"""
```

```python:src/mcp/__init__.py
"""
MCP (Model Context Protocol) integration
"""
```

```python:src/llm/__init__.py
"""
LLM integration using LangChain
"""
```

```python:src/api/__init__.py
"""
FastAPI application
"""
```

## Step 8: Verify Everything Works

Let's run our setup check again:

```bash
python scripts/check_setup.py
```

## Summary of What We've Done

✅ **Created virtual environment** (`venv`)  
✅ **Set up project structure** (src/, tests/, scripts/)  
✅ **Created configuration files** (.env.example, requirements.txt, README.md)  
✅ **Installed initial dependencies** (python-dotenv)  
✅ **Created environment file** (.env)  
✅ **Added package initialization files**  
✅ **Created setup verification script**  

## Next Steps

Once you've completed these steps and the setup check passes, we can move to **Phase 1: MCP Integration**. 

Let me know when you've completed these steps and I'll guide you through implementing the MCP client!

**Current Status**: ✅ Basic project setup complete  
**Next**: Phase 1 - MCP Integration (adding httpx and asyncio-subprocess dependencies) 