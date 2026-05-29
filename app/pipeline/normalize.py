from typing import Any, Dict, Optional


def normalize_acl(raw_acl: Optional[Dict[str, Any]], fallback_visibility: str = "internal") -> Dict[str, Any]:
    raw_acl = raw_acl or {}
    visibility = raw_acl.get("visibility", fallback_visibility)

    allowed_teams = raw_acl.get("allowed_teams", [])
    allowed_roles = raw_acl.get("allowed_roles", [])

    if not isinstance(allowed_teams, list):
        allowed_teams = []
    if not isinstance(allowed_roles, list):
        allowed_roles = []

    return {
        "visibility": visibility,
        "allowed_teams": allowed_teams,
        "allowed_roles": allowed_roles,
    }
