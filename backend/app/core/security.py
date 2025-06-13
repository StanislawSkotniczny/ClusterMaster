from typing import Optional
from fastapi import HTTPException, status

def verify_user_permissions(user_id: str, resource_id: Optional[str] = None) -> bool:
    """
    Verify if user has permissions to access resource
    """
    # Add your permission logic here
    return True

def get_current_user_id(token_data: dict) -> str:
    """
    Extract user ID from Firebase token data
    """
    return token_data.get("uid")