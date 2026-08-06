import datetime
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class PolicyCatalog(Base):
    __tablename__ = "policy_catalog"

    id = Column(Integer, primary_key=True, index=True)
    insurer_name = Column(String(100), nullable=False, index=True) # e.g., HDFC ERGO, Star Health, Niva Bupa, Care
    policy_name = Column(String(150), nullable=False, index=True) # e.g., Optima Secure, Optima Restore
    plan_variant = Column(String(100), nullable=True, default="Standard")
    
    # Feature specs
    base_sum_insured_min = Column(Float, default=500000.0) # 5L
    base_sum_insured_max = Column(Float, default=100000000.0) # 1Cr
    room_rent_limit = Column(String(100), default="Single Private Room (No Capping)")
    co_pay_percentage = Column(Float, default=0.0)
    ped_waiting_period_months = Column(Integer, default=36) # 36 months
    restoration_benefit = Column(String(250), default="100% Instant Unlimited Restore")
    no_claim_bonus = Column(String(250), default="50% per claim-free year up to 100%")
    
    pre_hospitalization_days = Column(Integer, default=60)
    post_hospitalization_days = Column(Integer, default=180)
    daycare_treatments_covered = Column(Boolean, default=True)
    organ_donor_cover = Column(Boolean, default=True)
    air_ambulance_cover = Column(Boolean, default=True)
    
    network_hospitals_count = Column(Integer, default=10000)
    claim_settlement_ratio = Column(Float, default=98.5) # %
    
    base_annual_premium_estimate = Column(Float, default=12500.0) # Estimated base price for 30yr old 10L
    brochure_pdf_path = Column(String(255), nullable=True)
    
    description = Column(Text, nullable=True)
    key_highlights = Column(Text, nullable=True) # JSON list
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ClaimCheckLog(Base):
    __tablename__ = "claim_check_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    policy_name = Column(String(150), nullable=False)
    hospital_name = Column(String(150), nullable=True)
    hospital_type = Column(String(50), default="Network") # Network vs Non-Network
    treatment_name = Column(String(150), nullable=False)
    claimed_amount = Column(Float, nullable=False)
    policy_duration_months = Column(Integer, default=12)
    is_ped_related = Column(Boolean, default=False)
    
    # Diagnosis / Result
    approval_eligibility = Column(String(50), nullable=False) # Eligible, Partially Eligible, Excluded
    estimated_approved_amount = Column(Float, nullable=False)
    deduction_reason = Column(Text, nullable=True)
    citations = Column(Text, nullable=True) # JSON array of citations
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="claim_checks")
