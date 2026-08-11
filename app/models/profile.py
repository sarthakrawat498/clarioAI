import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Profile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True) # Male, Female, Other
    city = Column(String(100), nullable=True)
    city_tier = Column(String(20), nullable=True) # Tier 1, Tier 2, Tier 3
    
    # Health Profile
    pre_existing_diseases = Column(Text, nullable=True, default="[]") # JSON string of diseases
    tobacco_user = Column(Boolean, default=False)
    bmi = Column(Float, nullable=True)
    
    # Insurance Preferences
    coverage_type = Column(String(50), nullable=True) # Individual, Family Floater
    family_members_count = Column(Integer, nullable=True)
    sum_insured_preference = Column(Float, nullable=True)
    budget_annual_max = Column(Float, nullable=True)
    preferred_room_type = Column(String(50), nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="profile")
