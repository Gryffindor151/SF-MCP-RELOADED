"""
Simple bearer token authentication
"""

import logging
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..core.config import config

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """Verify bearer token"""
    
    expected_token = config.API_BEARER_TOKEN
    
    if not expected_token:
        logger.warning("No API_BEARER_TOKEN configured - allowing access")
        return {"user_id": "dev_user", "authenticated": True}
    
    if credentials.credentials != expected_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "user_id": "api_user",
        "authenticated": True,
        "token_type": "bearer"
    } 