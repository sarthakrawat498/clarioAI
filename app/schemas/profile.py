from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class ProfileBase(BaseModel):
    age: Optional[int] = Field(default=None, ge=18, le=100)
    gender: Optional[str] = None
    city: Optional[str] = None
    city_tier: Optional[str] = None
    pre_existing_diseases: Optional[List[str]] = []
    tobacco_user: Optional[bool] = False
    bmi: Optional[float] = None
    coverage_type: Optional[str] = None
    family_members_count: Optional[int] = None
    sum_insured_preference: Optional[float] = None
    budget_annual_max: Optional[float] = None
    preferred_room_type: Optional[str] = None

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(ProfileBase):
    pass

class ProfileOut(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
