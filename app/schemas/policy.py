from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class PolicyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    insurer_name: str
    policy_name: str
    plan_variant: Optional[str] = "Standard"
    base_sum_insured_min: float
    base_sum_insured_max: float
    room_rent_limit: Optional[str] = None
    co_pay_percentage: Optional[float] = None
    ped_waiting_period_months: Optional[int] = None
    restoration_benefit: Optional[str] = None
    no_claim_bonus: Optional[str] = None
    pre_hospitalization_days: Optional[int] = None
    post_hospitalization_days: Optional[int] = None
    daycare_treatments_covered: bool
    organ_donor_cover: bool
    air_ambulance_cover: bool
    network_hospitals_count: Optional[int] = None
    claim_settlement_ratio: Optional[float] = None
    base_annual_premium_estimate: Optional[float] = None
    description: Optional[str] = None
    key_highlights: Optional[str] = None

class PolicyCompareRequest(BaseModel):
    policy_ids: List[int] = Field(..., min_length=2, max_length=4)

class PolicyCompareResponse(BaseModel):
    policies: List[PolicyOut]
    matrix: Dict[str, Dict[str, Any]]
    verdict: str
