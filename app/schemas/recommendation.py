from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class PremiumEstimateRequest(BaseModel):
    age: int = Field(default=30, ge=18, le=100)
    city_tier: str = Field(default="Tier 1") # Tier 1, Tier 2, Tier 3
    sum_insured: float = Field(default=1000000.0) # 10 Lakhs
    coverage_type: str = Field(default="Individual") # Individual, Family Floater
    family_members_count: int = Field(default=1)
    pre_existing_diseases: List[str] = Field(default_factory=list)
    tobacco_user: bool = Field(default=False)
    add_on_riders: List[str] = Field(default_factory=list) # e.g. ["Critical Illness", "Hospital Cash", "Maternity"]
    policy_id: Optional[int] = None
    policy_name: Optional[str] = None

class PremiumBreakdownItem(BaseModel):
    name: str
    amount: float
    description: str

class PremiumEstimateResponse(BaseModel):
    total_annual_premium: float
    base_premium: float
    gst_18_percent: float
    monthly_installment: float
    breakdown: List[PremiumBreakdownItem]
    policy_name: str = "Estimated Standard Health Policy"

class ScoredPolicyCard(BaseModel):
    policy_id: int
    insurer_name: str
    policy_name: str
    match_score: int # 0 to 100%
    estimated_annual_premium: float
    key_features: List[str]
    why_recommended: str
    suitable_for: str
    recommended_riders: List[str]

class RecommendationResponse(BaseModel):
    user_profile_summary: Dict[str, Any]
    top_recommendations: List[ScoredPolicyCard]
    general_advice: str
