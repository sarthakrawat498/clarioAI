from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class ProfileBase(BaseModel):
    age: Optional[int] = Field(default=30, ge=18, le=100)
    gender: Optional[str] = "Male"
    city: Optional[str] = "Mumbai"
    city_tier: Optional[str] = "Tier 1"
    pre_existing_diseases: Optional[List[str]] = []
    tobacco_user: Optional[bool] = False
    bmi: Optional[float] = 22.5
    coverage_type: Optional[str] = "Family Floater"
    family_members_count: Optional[int] = 2
    sum_insured_preference: Optional[float] = 1000000.0
    budget_annual_max: Optional[float] = 25000.0
    preferred_room_type: Optional[str] = "Single Private Room"

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(ProfileBase):
    pass

class ProfileOut(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
