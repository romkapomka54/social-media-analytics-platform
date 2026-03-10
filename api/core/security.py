"""
Security utilities (JWT, authentication, etc.).
"""
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


async def get_current_tenant(
    credentials: Optional[HTTPAuthorizationCredentials] = None
) -> Optional[str]:
    """
    Extract tenant ID from request (future implementation).
    For now, returns None (open API for testing).
    """
    # TODO: Implement JWT validation or API key validation
    # For now, we'll allow open access for testing
    return None


def require_tenant(tenant_id: Optional[str]) -> str:
    """Require tenant ID for operations."""
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant ID is required"
        )
    return tenant_id
