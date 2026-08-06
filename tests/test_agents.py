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
