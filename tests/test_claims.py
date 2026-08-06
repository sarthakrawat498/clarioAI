import pytest
from app.schemas.claim import ClaimCheckRequest
from app.services.claim_service import evaluate_claim_eligibility


def test_claim_initial_waiting_period_exclusion():
    """Test claim rejection under 30-day initial waiting period."""
    req = ClaimCheckRequest(
        policy_name="HDFC ERGO Optima Secure",
        treatment_name="Appendectomy",
        claimed_amount=50000.0,
        policy_holding_duration_months=0, # 0 months = initial waiting period
        is_pre_existing_condition=False
    )
    res = evaluate_claim_eligibility(req)
    
    assert res.status == "Excluded"
    assert res.estimated_approved_amount == 0.0
    assert "initial 30-day" in res.warnings[0].lower()


def test_claim_cataract_sublimit():
    """Test Cataract claim evaluation with capping."""
    req = ClaimCheckRequest(
        policy_name="Star Health Optima Restore",
        treatment_name="Cataract Surgery",
        claimed_amount=70000.0,
        policy_holding_duration_months=25, # Passed 24-mo waiting period
        is_pre_existing_condition=False
    )
    res = evaluate_claim_eligibility(req)
    
    assert res.status == "Partially Eligible"
    assert res.estimated_approved_amount == 40000.0
    assert res.deductions == 30000.0
