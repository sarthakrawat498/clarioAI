from types import SimpleNamespace

import pytest
from app.config import settings
from app.agents.graph import run_agent_workflow, route_intent
from app.agents import sales_agent as sales_agent_module


def test_multi_agent_routing_coverage():
    """Test router agent intent classification and coverage agent node execution."""
    output = run_agent_workflow(
        query="Does HDFC ERGO Optima Secure cover robotic surgery?",
        user_profile={"age": 30}
    )
    
    assert output["intent"] in ["COVERAGE", "FAQ"]
    assert "CoverageAgent" in output["agent_used"] or "RouterAgent" in output["agent_used"]
    assert len(output["final_response"]) > 20


def test_multi_agent_comparison():
    """Test comparison agent matrix generation."""
    output = run_agent_workflow(
        query="Compare HDFC Optima Secure and Star Health Optima Restore side by side",
        user_profile={"age": 35}
    )
    
    assert output["intent"] == "COMPARISON"
    assert "ComparisonAgent" in output["agent_used"]
    assert "Matrix" in output["final_response"] or "Side-by-Side" in output["final_response"]


def test_route_intent_maps_premium_and_claim():
    assert route_intent({"intent": "PREMIUM"}) == "premium"
    assert route_intent({"intent": "CLAIM"}) == "claim"
    assert route_intent({"intent": "FAQ", "claim_amount": 300000}) == "claim"
    assert route_intent({"intent": "SALES"}) == "sales"
    assert route_intent({"intent": "CATALOG"}) == "catalog"
    assert route_intent({"intent": "FAQ"}) == "chat"


def test_premium_query_routes_to_premium_agent(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "", raising=False)
    monkeypatch.setattr(
        "app.agents.graph.calculate_actuarial_premium",
        lambda req: SimpleNamespace(
            policy_name=req.policy_name,
            total_annual_premium=18000.0,
            base_premium=15254.0,
            gst_18_percent=2745.72,
            monthly_installment=1500.0,
            breakdown=[SimpleNamespace(name="Base Premium", amount=15254.0, description="Selected policy rate")],
        ),
    )

    output = run_agent_workflow(
        query="calculate premium for HDFC ERGO Optima Secure",
        user_profile={
            "age": 34,
            "gender": "Male",
            "city_tier": "Tier 1",
            "coverage_type": "Family Floater",
            "family_members_count": 3,
            "sum_insured_preference": 1000000,
            "pre_existing_diseases": ["diabetes"],
            "tobacco_user": False,
        },
        policy_catalog=[
            {
                "policy_id": 1,
                "insurer_name": "HDFC ERGO",
                "policy_name": "Optima Secure",
                "base_annual_premium_estimate": 15254.0,
                "room_rent_limit": "Single Private Room",
                "ped_waiting_period_months": 36,
                "claim_settlement_ratio": 98.5,
                "network_hospitals_count": 10000,
            }
        ],
    )

    assert output["intent"] == "PREMIUM"
    assert "PremiumAgent" in output["agent_used"]
    assert "Premium Estimate" in output["final_response"]
    assert "Total Annual Premium" in output["final_response"]


def test_claim_query_routes_to_claim_agent(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "", raising=False)
    monkeypatch.setattr(
        "app.agents.graph.evaluate_policy_claim_amount_coverage",
        lambda **kwargs: {
            "status": "YES",
            "covered": True,
            "supported_limit": 500000.0,
            "best_evidence": [
                {
                    "page": 12,
                    "snippet": "Robotic Surgery & Modern Treatments: Covers robotic surgeries up to 100% sum insured.",
                    "limit": 500000.0,
                }
            ],
            "explanation": "The strongest supported hospital/surgery limit found for this policy is ₹5,00,000.",
        },
    )

    output = run_agent_workflow(
        query="check claim eligibility for cataract surgery on HDFC ERGO Optima Secure with claim of ₹70,000",
        user_profile={
            "age": 45,
            "gender": "Female",
            "city_tier": "Tier 1",
            "coverage_type": "Family Floater",
            "family_members_count": 2,
            "sum_insured_preference": 1000000,
            "pre_existing_diseases": [],
            "policy_holding_duration_months": 25,
        },
        policy_catalog=[
            {
                "policy_id": 1,
                "insurer_name": "HDFC ERGO",
                "policy_name": "Optima Secure",
                "base_sum_insured_max": 1000000.0,
                "room_rent_limit": "Single Private Room",
                "co_pay_percentage": 0.0,
                "ped_waiting_period_months": 36,
                "pre_hospitalization_days": 60,
                "post_hospitalization_days": 180,
                "network_hospitals_count": 10000,
                "claim_settlement_ratio": 98.5,
            }
        ],
    )

    assert output["intent"] == "CLAIM"
    assert "ClaimAgent" in output["agent_used"]
    assert "Claim Amount Check" in output["final_response"]
    assert "Result:" in output["final_response"]


def test_compare_query_uses_explicit_selected_policies(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "", raising=False)

    policy_catalog = [
        {
            "policy_id": 1,
            "insurer_name": "HDFC ERGO",
            "policy_name": "Optima Secure",
            "room_rent_limit": "Single Private Room",
            "co_pay_percentage": 0.0,
            "ped_waiting_period_months": 36,
            "restoration_benefit": "100% Restore",
            "no_claim_bonus": "50%",
            "pre_hospitalization_days": 60,
            "post_hospitalization_days": 180,
            "daycare_treatments_covered": True,
            "air_ambulance_cover": True,
            "base_annual_premium_estimate": 14500,
            "description": "Policy 1",
            "claim_settlement_ratio": 98.5,
            "network_hospitals_count": 10000,
        },
        {
            "policy_id": 2,
            "insurer_name": "Star Health",
            "policy_name": "Optima Restore",
            "room_rent_limit": "Single Private Room",
            "co_pay_percentage": 0.0,
            "ped_waiting_period_months": 48,
            "restoration_benefit": "100% Restore",
            "no_claim_bonus": "20%",
            "pre_hospitalization_days": 60,
            "post_hospitalization_days": 90,
            "daycare_treatments_covered": True,
            "air_ambulance_cover": True,
            "base_annual_premium_estimate": 12800,
            "description": "Policy 2",
            "claim_settlement_ratio": 96.5,
            "network_hospitals_count": 9000,
        },
        {
            "policy_id": 3,
            "insurer_name": "Care Health",
            "policy_name": "Care Supreme",
            "room_rent_limit": "No Capping",
            "co_pay_percentage": 0.0,
            "ped_waiting_period_months": 36,
            "restoration_benefit": "Unlimited",
            "no_claim_bonus": "500%",
            "pre_hospitalization_days": 60,
            "post_hospitalization_days": 180,
            "daycare_treatments_covered": True,
            "air_ambulance_cover": True,
            "base_annual_premium_estimate": 13200,
            "description": "Policy 3",
            "claim_settlement_ratio": 97.5,
            "network_hospitals_count": 11000,
        },
    ]

    output = run_agent_workflow(
        query="Compare selected policies side by side",
        policy_catalog=policy_catalog,
        compare_policy_ids=[2, 3],
        user_profile={"age": 30},
    )

    assert output["intent"] == "COMPARISON"
    assert "ComparisonAgent" in output["agent_used"]
    assert output["comparison_table"] is not None
    assert list(output["comparison_table"]["Insurer"].keys()) == ["Star Health Optima Restore", "Care Health Care Supreme"]
    assert "HDFC ERGO Optima Secure" not in output["final_response"]


def test_compare_query_appends_uploaded_policy_column(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "", raising=False)

    policy_catalog = [
        {
            "policy_id": 1,
            "insurer_name": "HDFC ERGO",
            "policy_name": "Optima Secure",
            "room_rent_limit": "Single Private Room",
            "co_pay_percentage": 0.0,
            "ped_waiting_period_months": 36,
            "restoration_benefit": "100% Restore",
            "no_claim_bonus": "50%",
            "pre_hospitalization_days": 60,
            "post_hospitalization_days": 180,
            "daycare_treatments_covered": True,
            "air_ambulance_cover": True,
            "base_annual_premium_estimate": 14500,
            "description": "Policy 1",
            "claim_settlement_ratio": 98.5,
            "network_hospitals_count": 10000,
        },
        {
            "policy_id": 2,
            "insurer_name": "Star Health",
            "policy_name": "Optima Restore",
            "room_rent_limit": "Single Private Room",
            "co_pay_percentage": 0.0,
            "ped_waiting_period_months": 48,
            "restoration_benefit": "100% Restore",
            "no_claim_bonus": "20%",
            "pre_hospitalization_days": 60,
            "post_hospitalization_days": 90,
            "daycare_treatments_covered": True,
            "air_ambulance_cover": True,
            "base_annual_premium_estimate": 12800,
            "description": "Policy 2",
            "claim_settlement_ratio": 96.5,
            "network_hospitals_count": 9000,
        },
    ]

    uploaded_policy_baseline = {
        "source_file_name": "my_uploaded_policy.pdf",
        "policy_name": "My Uploaded Policy",
        "uploaded_premium": 22000,
        "uploaded_sum_assured": 1500000,
        "benefits": ["No room rent capping", "100% restore benefit", "Cashless hospitalization"],
        "extracted_summary": {
            "room_rent_limit": "No room rent capping",
            "restoration_benefit": "100% restore benefit",
            "no_claim_bonus": "50% bonus",
            "ped_waiting_period_months": 24,
            "pre_hospitalization_days": 60,
            "post_hospitalization_days": 180,
            "daycare_treatments_covered": True,
            "air_ambulance_cover": True,
            "claim_settlement_ratio": 97.0,
            "network_hospitals_count": 12000,
        },
    }

    output = run_agent_workflow(
        query="Compare my uploaded policy with one policy",
        policy_catalog=policy_catalog,
        compare_policy_ids=[2],
        uploaded_policy_baseline=uploaded_policy_baseline,
        user_profile={"age": 30},
    )

    assert output["intent"] == "COMPARISON"
    assert "ComparisonAgent" in output["agent_used"]
    assert output["comparison_table"] is not None
    assert list(output["comparison_table"]["Insurer"].keys()) == ["Star Health Optima Restore", "My Uploaded Policy"]
    assert output["comparison_table"]["Room Rent Category"]["My Uploaded Policy"] == "No room rent capping"
    assert output["comparison_table"]["Co-Payment"]["My Uploaded Policy"] == "10.0%"
    assert output["comparison_table"]["PED Waiting Period"]["My Uploaded Policy"] == "24 Months"
    assert "My Uploaded Policy" in output["final_response"]


def test_yes_followup_after_sales_routes_to_comparison():
    """Short affirmative follow-up after SalesAgent output should trigger comparison flow."""
    sales_reply = (
        "#### 🛡️ Top AI Recommended Health Insurance Plans\n"
        "#### 1. Niva Bupa - Aspire (Match Score: 85%)\n"
        "#### 2. Aditya Birla - Activ One (Match Score: 80%)\n"
        "#### 3. Care Health - Care Supreme (Match Score: 79%)\n"
        "Would you like to run a side-by-side comparison of these plans or check custom claim scenarios?"
    )

    output = run_agent_workflow(
        query="yes",
        messages=[
            {"role": "assistant", "content": sales_reply, "agent_name": "SalesAgent (AI Actuarial & RAG)"},
            {"role": "user", "content": "yes"},
        ],
        user_profile={"age": 30, "budget_annual_max": 12700},
    )

    assert output["intent"] == "COMPARISON"
    assert "ComparisonAgent" in output["agent_used"]
    assert output.get("comparison_table") is not None


def _base_sales_state(policy_catalog, budget, sum_insured):
    profile = {
        "age": 30,
        "gender": "Male",
        "city": "Mumbai",
        "coverage_type": "Family Floater",
        "sum_insured_preference": sum_insured,
        "budget_annual_max": budget,
        "pre_existing_diseases": [],
    }
    return {
        "query": "recommend best health policy for my profile",
        "age": profile["age"],
        "gender": profile["gender"],
        "city": profile["city"],
        "coverage_type": profile["coverage_type"],
        "sum_insured_preference": profile["sum_insured_preference"],
        "budget_annual_max": profile["budget_annual_max"],
        "pre_existing_diseases": profile["pre_existing_diseases"],
        "user_profile": profile,
        "policy_catalog": policy_catalog,
        "uploaded_policy_baseline": {},
    }


def _make_policy(premium, max_sum_insured):
    return {
        "policy_id": 1,
        "insurer_name": "Test Insurer",
        "policy_name": "Test Plan",
        "base_annual_premium_estimate": premium,
        "base_sum_insured_min": 500000,
        "base_sum_insured_max": max_sum_insured,
        "room_rent_limit": "No Capping",
        "restoration_benefit": "Unlimited Restore",
        "no_claim_bonus": "50% per year",
        "network_hospitals_count": 10000,
        "claim_settlement_ratio": 98.5,
        "ped_waiting_period_months": 36,
        "co_pay_percentage": 0.0,
        "description": "Test policy",
        "key_highlights": ["Test highlight"],
    }


@pytest.mark.parametrize(
    "premium,budget,max_sum_insured,sum_insured,expected_eligible",
    [
        (20000, 20000, 1000000, 1000000, True),
        (15000, 20000, 1000000, 1000000, True),
        (21000, 20000, 1000000, 1000000, True),
        (15000, 20000, 1000000, 1000000, True),
        (15000, 20000, 2000000, 1000000, True),
        (15000, 20000, 900000, 1000000, False),
        (15000, 20000, 2000000, 1000000, True),
        (15000, 20000, 900000, 1000000, False),
        (25000, 20000, 2000000, 1000000, True),
        (25000, 20000, 900000, 1000000, False),
        (26000, 20000, 2000000, 1000000, False),
    ],
)
def test_sales_agent_hard_eligibility_boundaries(monkeypatch, premium, budget, max_sum_insured, sum_insured, expected_eligible):
    monkeypatch.setattr(sales_agent_module.vector_store_manager, "query", lambda **kwargs: [])
    monkeypatch.setattr(sales_agent_module.settings, "OPENAI_API_KEY", "", raising=False)

    state = _base_sales_state([
        _make_policy(premium=premium, max_sum_insured=max_sum_insured)
    ], budget=budget, sum_insured=sum_insured)
    output = sales_agent_module.sales_agent_node(state)

    if expected_eligible:
        assert len(output["recommended_policies"]) == 1
        assert output["recommended_policies"][0]["policy_name"] == "Test Plan"
        assert "No Eligible Policies Found" not in output["final_response"]
    else:
        assert output["recommended_policies"] == []
        assert "No Eligible Policies Found" in output["final_response"]


def test_sales_agent_no_eligible_policies(monkeypatch):
    monkeypatch.setattr(sales_agent_module.vector_store_manager, "query", lambda **kwargs: [])
    monkeypatch.setattr(sales_agent_module.settings, "OPENAI_API_KEY", "", raising=False)

    state = _base_sales_state([], budget=1, sum_insured=1000000)
    output = sales_agent_module.sales_agent_node(state)

    assert output["recommended_policies"] == []
    assert "No Eligible Policies Found" in output["final_response"]


def test_sales_agent_uploaded_policy_does_not_override_saved_profile(monkeypatch):
    monkeypatch.setattr(sales_agent_module.vector_store_manager, "query", lambda **kwargs: [])
    monkeypatch.setattr(sales_agent_module.settings, "OPENAI_API_KEY", "", raising=False)

    state = _base_sales_state(
        [
            _make_policy(premium=23000, max_sum_insured=1500000),
        ],
        budget=15000,
        sum_insured=1000000,
    )
    state["uploaded_policy_baseline"] = {
        "uploaded_premium": 25000,
        "uploaded_sum_assured": 1500000,
        "effective_budget": 25000,
        "target_sum_insured": 1500000,
        "premium_floor": 20000,
        "premium_ceiling": 30000,
        "use_uploaded_policy_as_primary": True,
    }

    output = sales_agent_module.sales_agent_node(state)

    assert output["recommended_policies"] == []
    assert "No Eligible Policies Found" in output["final_response"]


def test_sales_agent_uploaded_policy_never_changes_budget_window(monkeypatch):
    monkeypatch.setattr(sales_agent_module.vector_store_manager, "query", lambda **kwargs: [])
    monkeypatch.setattr(sales_agent_module.settings, "OPENAI_API_KEY", "", raising=False)

    state = _base_sales_state(
        [
            _make_policy(premium=18000, max_sum_insured=1000000),
            _make_policy(premium=22000, max_sum_insured=1000000),
        ],
        budget=15000,
        sum_insured=1000000,
    )
    state["uploaded_policy_baseline"] = {
        "uploaded_premium": 25000,
        "uploaded_sum_assured": 1000000,
        "effective_budget": 25000,
        "target_sum_insured": 1000000,
        "use_uploaded_policy_as_primary": True,
    }

    output = sales_agent_module.sales_agent_node(state)

    assert [plan["est_premium"] for plan in output["recommended_policies"]] == [18000.0]
    assert "uploaded policy" not in output["final_response"].lower()
