from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ClaimCheckRequest(BaseModel):
    policy_name: str = Field(..., description="Target policy e.g. Star Health Optima Restore")
    treatment_name: str = Field(..., description="e.g. Cataract Surgery, Appendectomy, Diabetes Complications")
    claimed_amount: float = Field(..., gt=0)
    hospital_name: Optional[str] = "Apollo Hospital"
    hospital_type: str = Field(default="Network", description="Network or Non-Network")
    room_category_chosen: str = Field(default="Single Private Room", description="Single Private Room, Shared, Suite")
    policy_holding_duration_months: int = Field(default=12, ge=0)
    is_pre_existing_condition: bool = Field(default=False)
    ped_disclosed_at_purchase: bool = Field(default=True)

class ClaimCheckResponse(BaseModel):
    status: str # Eligible, Partially Eligible, Excluded
    estimated_approved_amount: float
    deductions: float
    coverage_breakdown: Dict[str, Any]
    warnings: List[str]
    citations: List[Dict[str, Any]]
    explanation: str
