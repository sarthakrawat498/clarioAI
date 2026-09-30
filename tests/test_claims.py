from types import SimpleNamespace

import pytest

from app.schemas.claim import ClaimCheckRequest
from app.services import claim_service
from app.services.claim_service import (
    evaluate_claim_eligibility,
    evaluate_policy_claim_amount_coverage,
)


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


def test_claim_amount_coverage_yes_from_chunks(monkeypatch):
    monkeypatch.setattr(
        claim_service,
        "_find_policy_record",
        lambda policy_name: SimpleNamespace(
            insurer_name="HDFC ERGO",
            policy_name="Optima Secure",
            base_sum_insured_max=1000000.0,
        ),
    )
    monkeypatch.setattr(
        claim_service.vector_store_manager,
        "query",
        lambda **kwargs: [
            {
                "company": "HDFC ERGO",
                "policy_name": "Optima Secure",
                "page": 12,
                "chunk_id": "chunk-1",
                "content": "Robotic Surgery & Modern Treatments: Covers robotic surgeries up to 100% sum insured.",
                "citation": "[Company: HDFC ERGO, Policy: Optima Secure, Page: 12]",
            },
            {
                "company": "HDFC ERGO",
                "policy_name": "Optima Secure",
                "page": 14,
                "chunk_id": "chunk-2",
                "content": "Daycare Treatments are covered up to full sum insured.",
                "citation": "[Company: HDFC ERGO, Policy: Optima Secure, Page: 14]",
            },
        ],
    )

    res = evaluate_policy_claim_amount_coverage(
        policy_name="HDFC ERGO Optima Secure",
        claimed_amount=300000.0,
        treatment_name="Hospitalization",
    )

    assert res["status"] == "YES"
    assert res["covered"] is True
    assert res["supported_limit"] == 1000000.0
    assert len(res["best_evidence"]) == 2


def test_claim_amount_coverage_no_from_lower_limit(monkeypatch):
    monkeypatch.setattr(
        claim_service,
        "_find_policy_record",
        lambda policy_name: SimpleNamespace(
            insurer_name="Star Health",
            policy_name="Optima Restore",
            base_sum_insured_max=500000.0,
        ),
    )
    monkeypatch.setattr(
        claim_service.vector_store_manager,
        "query",
        lambda **kwargs: [
            {
                "company": "Star Health",
                "policy_name": "Optima Restore",
                "page": 18,
                "chunk_id": "chunk-9",
                "content": "Cataract Sub-Limit: Cataract surgery limited to INR 40,000 per eye.",
                "citation": "[Company: Star Health, Policy: Optima Restore, Page: 18]",
            }
        ],
    )

    res = evaluate_policy_claim_amount_coverage(
        policy_name="Star Health Optima Restore",
        claimed_amount=70000.0,
        treatment_name="Cataract Surgery",
    )

    assert res["status"] == "NO"
    assert res["covered"] is False
    assert res["supported_limit"] == 40000.0


def test_claim_amount_coverage_missing_chunks(monkeypatch):
    monkeypatch.setattr(claim_service, "_find_policy_record", lambda policy_name: None)
    monkeypatch.setattr(claim_service.vector_store_manager, "query", lambda **kwargs: [])

    res = evaluate_policy_claim_amount_coverage(
        policy_name="Unknown Policy",
        claimed_amount=300000.0,
        treatment_name="Hospitalization",
    )

    assert res["status"] == "UNKNOWN"
    assert res["covered"] is None
    assert res["best_evidence"] == []
