import pytest
from app.agents.graph import run_agent_workflow


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
