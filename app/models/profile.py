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
    city_tier = Column(String(20), default="Tier 1") # Tier 1, Tier 2, Tier 3
    
    # Health Profile
    pre_existing_diseases = Column(Text, nullable=True, default="[]") # JSON string of diseases e.g., ["Diabetes", "Hypertension"]
    tobacco_user = Column(Boolean, default=False)
    bmi = Column(Float, nullable=True)
    
    # Insurance Preferences
    coverage_type = Column(String(50), default="Family Floater") # Individual, Family Floater
    family_members_count = Column(Integer, default=2)
    sum_insured_preference = Column(Float, default=1000000.0) # e.g. 10 Lakhs (1,000,000)
    budget_annual_max = Column(Float, nullable=True, default=25000.0) # e.g. 25,000 INR
    preferred_room_type = Column(String(50), default="Single Private Room") # Single Private, Shared, Suite
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="profile")
