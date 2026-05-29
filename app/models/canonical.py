from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class ACL(BaseModel):
    visibility: str  # internal | team | restricted
    allowed_teams: List[str] = Field(default_factory=list)
    allowed_roles: List[str] = Field(default_factory=list)


class Lineage(BaseModel):
    ingestion_run_id: str
    source_file: str
    parser_version: str


class CanonicalDoc(BaseModel):
    doc_id: str
    source_type: str         # incident | jira | kb | slack | oncall
    source_id: str
    title: str
    content: str
    timestamp: datetime
    updated_at: datetime
    owners: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    acl: ACL
    source_url: Optional[str] = None
    lineage: Lineage
    extra: Dict[str, Any] = Field(default_factory=dict)
