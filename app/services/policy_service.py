import json
import logging
from typing import List
from sqlalchemy.orm import Session
from app.models.policy import PolicyCatalog

logger = logging.getLogger(__name__)

INITIAL_CATALOG = [
    {
        "insurer_name": "HDFC ERGO",
        "policy_name": "Optima Secure",
        "plan_variant": "Secure Gold",
        "base_sum_insured_min": 500000.0,
        "base_sum_insured_max": 20000000.0,
        "room_rent_limit": "Single Private AC Room (No Capping)",
        "co_pay_percentage": 0.0,
        "ped_waiting_period_months": 36,
        "restoration_benefit": "100% Instant Automatic Restoration (Unlimited)",
        "no_claim_bonus": "50% in Year 1, 100% in Year 2 (Secure + Plus Benefit)",
        "pre_hospitalization_days": 60,
        "post_hospitalization_days": 180,
        "daycare_treatments_covered": True,
        "organ_donor_cover": True,
        "air_ambulance_cover": True,
        "network_hospitals_count": 13000,
        "claim_settlement_ratio": 99.1,
        "base_annual_premium_estimate": 14500.0,
        "description": "Doubles your sum insured instantly from day 1 and includes zero deduction on medical consumables.",
        "key_highlights": json.dumps(["2X Base Sum Insured", "Zero Consumable Deduction", "Unlimited Restore"])
    },
    {
        "insurer_name": "Care Health",
        "policy_name": "Care Supreme",
        "plan_variant": "Supreme Ultra",
        "base_sum_insured_min": 700000.0,
        "base_sum_insured_max": 50000000.0,
        "room_rent_limit": "No Room Rent Capping (Any Room Category)",
        "co_pay_percentage": 0.0,
        "ped_waiting_period_months": 36,
        "restoration_benefit": "Unlimited 100% Automatic Recharge",
        "no_claim_bonus": "50% per year up to 500% Super Bonus",
        "pre_hospitalization_days": 60,
        "post_hospitalization_days": 180,
        "daycare_treatments_covered": True,
        "organ_donor_cover": True,
        "air_ambulance_cover": True,
        "network_hospitals_count": 11500,
        "claim_settlement_ratio": 95.2,
        "base_annual_premium_estimate": 13200.0,
        "description": "Highest cumulative bonus potential (up to 5x base sum insured) with instant PED riders.",
        "key_highlights": json.dumps(["500% Cumulative Bonus", "Unlimited Recharge", "No Room Capping"])
    },
    {
        "insurer_name": "Niva Bupa",
        "policy_name": "ReAssure 2.0",
        "plan_variant": "Titanium",
        "base_sum_insured_min": 500000.0,
        "base_sum_insured_max": 100000000.0,
        "room_rent_limit": "Single Private Room",
        "co_pay_percentage": 0.0,
        "ped_waiting_period_months": 36,
        "restoration_benefit": "ReAssure Forever (Active lifetime after 1st claim)",
        "no_claim_bonus": "Lock the Premium until 1st claim",
        "pre_hospitalization_days": 60,
        "post_hospitalization_days": 180,
        "daycare_treatments_covered": True,
        "organ_donor_cover": True,
        "air_ambulance_cover": True,
        "network_hospitals_count": 10000,
        "claim_settlement_ratio": 98.2,
        "base_annual_premium_estimate": 13900.0,
        "description": "Locks your entry age premium forever until you make your first claim.",
        "key_highlights": json.dumps(["Lock the Premium", "ReAssure Forever", "30% Live Healthier Discount"])
    },
    {
        "insurer_name": "Star Health",
        "policy_name": "Optima Restore",
        "plan_variant": "Individual / Floater",
        "base_sum_insured_min": 500000.0,
        "base_sum_insured_max": 25000000.0,
        "room_rent_limit": "Single Private AC Room",
        "co_pay_percentage": 0.0,
        "ped_waiting_period_months": 48,
        "restoration_benefit": "100% Restore once per policy year",
        "no_claim_bonus": "20% per year up to 100%",
        "pre_hospitalization_days": 60,
        "post_hospitalization_days": 90,
        "daycare_treatments_covered": True,
        "organ_donor_cover": True,
        "air_ambulance_cover": True,
        "network_hospitals_count": 14000,
        "claim_settlement_ratio": 97.8,
        "base_annual_premium_estimate": 12800.0,
        "description": "Pan-India brand with largest network hospital presence and free annual health checkups.",
        "key_highlights": json.dumps(["14,000+ Cashless Hospitals", "Annual Health Checkup", "Restore Benefit"])
    }
]


def seed_policy_catalog(db: Session):
    """Seed initial policy database if empty."""
    if db.query(PolicyCatalog).count() == 0:
        for p in INITIAL_CATALOG:
            db.add(PolicyCatalog(**p))
        db.commit()
        logger.info("Policy catalog seeded with 4 flagship health plans.")


def get_all_policies(db: Session) -> List[PolicyCatalog]:
    """Fetch policy catalogue."""
    seed_policy_catalog(db)
    return db.query(PolicyCatalog).all()


def get_policy_by_id(db: Session, policy_id: int) -> PolicyCatalog:
    """Fetch policy by ID."""
    return db.query(PolicyCatalog).filter(PolicyCatalog.id == policy_id).first()
