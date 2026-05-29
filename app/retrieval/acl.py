from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Set

# Teams that represent authenticated TechCorp employees in the synthetic corpus.
EMPLOYEE_TEAMS: Set[str] = {"platform", "payments", "search", "ml_infra", "security"}


@dataclass
class ACLContext:
    user_id: str
    team: str
    role: str
    clearance: str = "internal"


def is_employee(ctx: ACLContext) -> bool:
    return ctx.team in EMPLOYEE_TEAMS


def _normalize_acl(acl: Dict[str, Any]) -> Dict[str, Any]:
    acl = acl or {}
    visibility = acl.get("visibility", "internal")
    allowed_teams = acl.get("allowed_teams", []) or []
    allowed_roles = acl.get("allowed_roles", []) or []
    return {
        "visibility": visibility,
        "allowed_teams": allowed_teams,
        "allowed_roles": allowed_roles,
    }


def can_access(doc_acl: Dict[str, Any], ctx: ACLContext) -> bool:
    acl = _normalize_acl(doc_acl)
    visibility = acl["visibility"]
    allowed_teams = set(acl["allowed_teams"])
    allowed_roles = set(acl["allowed_roles"])

    team_match = ctx.team in allowed_teams if allowed_teams else False
    role_match = ctx.role in allowed_roles if allowed_roles else False

    if visibility == "internal":
        if allowed_teams or allowed_roles:
            return team_match or role_match
        # General internal docs: employees only (deny external/unauthenticated personas).
        return is_employee(ctx)

    if visibility in {"team", "restricted"}:
        return team_match or role_match

    return False


def filter_acl_docs(docs: Iterable[Dict[str, Any]], ctx: ACLContext) -> List[Dict[str, Any]]:
    return [doc for doc in docs if can_access(doc.get("acl", {}), ctx)]
