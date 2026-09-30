import pytest

from app.services import policy_service


def test_build_catalog_payload_uses_known_policy_fallback(monkeypatch):
    monkeypatch.setattr(policy_service, "_read_text", lambda file_path: "Policy document text without clean extraction fields.")

    payload = policy_service._build_catalog_payload(
        {
            "company": "HDFC ERGO",
            "policy_name": "Optima Secure",
            "file_path": "dummy.pdf",
            "filename": "dummy.pdf",
        }
    )

    assert payload["room_rent_limit"] == "Single Private Air-Conditioned Room"
    assert payload["restoration_benefit"] == "100% automatic restore benefit"
    assert payload["no_claim_bonus"] == "50% in Year 1, 100% in Year 2"
    assert payload["ped_waiting_period_months"] == 36
    assert payload["network_hospitals_count"] == 10000
    assert payload["base_annual_premium_estimate"] == 14500.0


def test_build_catalog_payload_rejects_definition_as_room_rent(monkeypatch):
    monkeypatch.setattr(
        policy_service,
        "_read_text",
        lambda file_path: (
            "POLICY WORDINGS: ACTIV ONE PLAN\n"
            "2.1 Room Rent Limit: means the amount charged by a Hospital towards Room and Boarding expenses and shall include the associated medical expenses.\n"
            "2.2 Co-Payment: 0%"
        ),
    )

    payload = policy_service._build_catalog_payload(
        {
            "company": "Aditya Birla",
            "policy_name": "Activ One",
            "file_path": "dummy.pdf",
            "filename": "dummy.pdf",
        }
    )

    assert payload["room_rent_limit"] is None
    assert payload["co_pay_percentage"] == 0.0
    assert payload["base_annual_premium_estimate"] is None
