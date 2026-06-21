"""Authentication and authorization provider for AyushBot Cloud API."""

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from cloud.api.exceptions import ForbiddenError, UnauthorizedError

# Demo API keys (in production, use database + hashing)
VALID_API_KEYS = {
    "admin-key-12345": {"role": "admin", "name": "Admin User"},
    "officer-key-67890": {"role": "officer", "name": "Health Officer"},
    "read-only-key-11111": {"role": "reader", "name": "Read-Only User"},
}

# Valid roles
VALID_ROLES = {"admin", "officer", "reader", "anonymous"}


class APIKeyAuth:
    """API Key authentication scheme."""

    def __init__(self):
        self.scheme = HTTPBearer()

    async def __call__(
        self, credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
    ) -> Optional[dict]:
        """Validate API key from Authorization header.
        
        Args:
            credentials: HTTP Bearer credentials
            
        Returns:
            User dict with role and name, or None if not authenticated
            
        Raises:
            UnauthorizedError: If credentials invalid
        """
        if credentials is None:
            return None

        api_key = credentials.credentials

        if api_key not in VALID_API_KEYS:
            raise UnauthorizedError(f"Invalid API key")

        return VALID_API_KEYS[api_key]


def get_current_user(
    authorization: Optional[str] = Header(None),
) -> Optional[dict]:
    """Get current user from Authorization header.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        User dict with role and name, or None if not authenticated
        
    Raises:
        UnauthorizedError: If credentials invalid
    """
    if authorization is None:
        return None

    # Parse "Bearer <api_key>" format
    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("Invalid authorization format. Use 'Bearer <api_key>'")

    api_key = authorization.replace("Bearer ", "", 1)

    if api_key not in VALID_API_KEYS:
        raise UnauthorizedError("Invalid API key")

    return VALID_API_KEYS[api_key]


def require_role(*allowed_roles: str):
    """FastAPI dependency to enforce role-based access control.
    
    Args:
        allowed_roles: One or more allowed roles (e.g., "admin", "officer")
        
    Returns:
        Dependency function for FastAPI
        
    Example:
        @app.get("/admin")
        async def admin_only(user = Depends(require_role("admin"))):
            return {"message": "Admin only"}
    """

    async def check_role(
        authorization: Optional[str] = Header(None),
    ) -> dict:
        """Check if user has required role.
        
        Args:
            authorization: Authorization header value
            
        Returns:
            User dict
            
        Raises:
            UnauthorizedError: If not authenticated
            ForbiddenError: If role not allowed
        """
        if authorization is None:
            raise UnauthorizedError("Missing authorization header")

        if not authorization.startswith("Bearer "):
            raise UnauthorizedError("Invalid authorization format")

        api_key = authorization.replace("Bearer ", "", 1)

        if api_key not in VALID_API_KEYS:
            raise UnauthorizedError("Invalid API key")

        user = VALID_API_KEYS[api_key]

        if user["role"] not in allowed_roles:
            raise ForbiddenError(
                f"User role '{user['role']}' not allowed. Required: {', '.join(allowed_roles)}"
            )

        return user

    return check_role


def require_admin():
    """Shorthand dependency for admin-only endpoints."""
    return require_role("admin")


def require_admin_or_officer():
    """Shorthand dependency for admin or officer."""
    return require_role("admin", "officer")


async def get_optional_user(
    authorization: Optional[str] = Header(None),
) -> Optional[dict]:
    """Get current user or None if not authenticated.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        User dict or None
    """
    if authorization is None:
        return None

    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("Invalid authorization format. Use 'Bearer <api_key>'")

    api_key = authorization.replace("Bearer ", "", 1)

    if api_key not in VALID_API_KEYS:
        raise UnauthorizedError("Invalid API key")

    return VALID_API_KEYS[api_key]
