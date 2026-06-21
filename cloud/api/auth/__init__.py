"""Authentication and authorization package for AyushBot Cloud API."""

from cloud.api.auth.cert_manager import CertificateManager
from cloud.api.auth.provider import (
    VALID_API_KEYS,
    VALID_ROLES,
    APIKeyAuth,
    get_current_user,
    get_optional_user,
    require_admin,
    require_admin_or_officer,
    require_role,
)

__all__ = [
    "CertificateManager",
    "VALID_API_KEYS",
    "VALID_ROLES",
    "APIKeyAuth",
    "get_current_user",
    "get_optional_user",
    "require_admin",
    "require_admin_or_officer",
    "require_role",
]

