from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class UploadedPolicyContext(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_file_name: str
    policy_name: Optional[str] = None
    sum_assured_amount: Optional[float] = None
    premium_amount: Optional[float] = None
    benefits: List[str] = []
    recommendation_window: Dict[str, Any] = {}
    extracted_summary: Dict[str, Any] = {}
    created_at: datetime


class UploadedPolicyUploadResponse(BaseModel):
    message: str
    session_id: int
    snapshot: UploadedPolicyContext
