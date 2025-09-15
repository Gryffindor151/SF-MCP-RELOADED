"""
Configuration management using environment variables
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Salesforce Configuration
    SALESFORCE_CONNECTION_TYPE: str = os.getenv("SALESFORCE_CONNECTION_TYPE", "User_Password")
    SALESFORCE_USERNAME: Optional[str] = os.getenv("SALESFORCE_USERNAME")
    SALESFORCE_PASSWORD: Optional[str] = os.getenv("SALESFORCE_PASSWORD")
    SALESFORCE_TOKEN: Optional[str] = os.getenv("SALESFORCE_TOKEN")
    SALESFORCE_INSTANCE_URL: Optional[str] = os.getenv("SALESFORCE_INSTANCE_URL")
    
    # Groq Configuration
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    
    # LLM Configuration
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1000"))
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "30"))
    
    @classmethod
    def get_salesforce_env_vars(cls) -> dict:
        """Get Salesforce environment variables for MCP server"""
        return {
            "SALESFORCE_CONNECTION_TYPE": cls.SALESFORCE_CONNECTION_TYPE,
            "SALESFORCE_USERNAME": cls.SALESFORCE_USERNAME,
            "SALESFORCE_PASSWORD": cls.SALESFORCE_PASSWORD,
            "SALESFORCE_TOKEN": cls.SALESFORCE_TOKEN,
            "SALESFORCE_INSTANCE_URL": cls.SALESFORCE_INSTANCE_URL
        }
    
    @classmethod
    def validate_salesforce_config(cls) -> list:
        """Validate required Salesforce configuration"""
        errors = []
        
        if not cls.SALESFORCE_USERNAME:
            errors.append("SALESFORCE_USERNAME is required")
        if not cls.SALESFORCE_PASSWORD:
            errors.append("SALESFORCE_PASSWORD is required")
        if not cls.SALESFORCE_TOKEN:
            errors.append("SALESFORCE_TOKEN is required")
        if not cls.SALESFORCE_INSTANCE_URL:
            errors.append("SALESFORCE_INSTANCE_URL is required")
        
        return errors
    
    @classmethod
    def validate_llm_config(cls) -> list:
        """Validate required LLM configuration"""
        errors = []
        
        if not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY is required")
        
        return errors

# Global config instance
config = Config() 