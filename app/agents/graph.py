import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.router_agent import router_agent_node
from app.agents.profile_agent import profile_agent_node
from app.agents.coverage_agent import coverage_agent_node
from app.agents.comparison_agent import comparison_agent_node
from app.agents.sales_agent import sales_agent_node
from app.agents.chat_agent import chat_agent_node

logger = logging.getLogger(__name__)


def route_intent(state: AgentState) -> str:
    """Conditional routing function returning next agent node key."""
    intent = state.get("intent", "FAQ").upper()
    if intent == "PROFILE":
        return "profile"
    elif intent == "COVERAGE":
        return "coverage"
    elif intent == "COMPARISON":
        return "comparison"
    elif intent == "SALES":
        return "sales"
    else:
        return "chat"


def build_health_insurance_graph():
    """Build and compile the LangGraph multi-agent workflow."""
    workflow = StateGraph(AgentState)

    # Register Nodes
    workflow.add_node("router", router_agent_node)
    workflow.add_node("profile", profile_agent_node)
    workflow.add_node("coverage", coverage_agent_node)
    workflow.add_node("comparison", comparison_agent_node)
    workflow.add_node("sales", sales_agent_node)
    workflow.add_node("chat", chat_agent_node)

    # Set Entry Point
    workflow.set_entry_point("router")

    # Add Conditional Edges from Router
    workflow.add_conditional_edges(
        "router",
        route_intent,
        {
            "profile": "profile",
            "coverage": "coverage",
            "comparison": "comparison",
            "sales": "sales",
            "chat": "chat"
        }
    )

    # Connect leaf nodes to END
    workflow.add_edge("profile", END)
    workflow.add_edge("coverage", END)
    workflow.add_edge("comparison", END)
    workflow.add_edge("sales", END)
    workflow.add_edge("chat", END)

    app_graph = workflow.compile()
    logger.info("LangGraph Health Insurance Multi-Agent workflow compiled successfully.")
    return app_graph


# Global Compiled Graph Singleton
agent_graph = build_health_insurance_graph()


def run_agent_workflow(
    query: str,
    user_profile: Dict[str, Any] = None,
    filter_company: str = None,
    filter_policy: str = None
) -> AgentState:
    """Convenience execution wrapper for multi-agent graph processing."""
    initial_state: AgentState = {
        "query": query,
        "user_profile": user_profile or {},
        "messages": [{"role": "user", "content": query}],
        "intent": "FAQ",
        "retrieved_docs": [],
        "sources": [],
        "final_response": "",
        "agent_used": "",
        "recommended_policies": None,
        "comparison_table": None,
        "filter_company": filter_company,
        "filter_policy": filter_policy
    }

    final_output = agent_graph.invoke(initial_state)
    return final_output
