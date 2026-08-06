from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class CitationSource(BaseModel):
    company: str
    policy_name: str
    page: int
    chunk_id: str
    snippet: str

class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1)

class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = []
    agent_name: Optional[str] = "ChatAgent"
    created_at: datetime

class ChatSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_title: str
    created_at: datetime
    messages: List[ChatMessageOut] = []

class ChatQueryRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[int] = None
    filter_company: Optional[str] = None
    filter_policy: Optional[str] = None

class ChatQueryResponse(BaseModel):
    session_id: int
    message: str
    agent_used: str
    intent: str
    sources: List[Dict[str, Any]] = []
    recommended_policies: Optional[List[Dict[str, Any]]] = None
    comparison_table: Optional[Dict[str, Any]] = None
