import logging
from app.config import settings
from app.agents.state import AgentState

logger = logging.getLogger(__name__)


_AFFIRMATIVE_FOLLOWUP_KEYWORDS = {
    "yes", "yeah", "yep", "ok", "okay", "sure", "alright", "proceed", "go ahead", "compare"
}


def _is_affirmative_followup(query_lower: str) -> bool:
    normalized = " ".join(query_lower.split())
    if not normalized or len(normalized) > 24:
        return False
    return any(token in normalized for token in _AFFIRMATIVE_FOLLOWUP_KEYWORDS)


def _last_assistant_message(messages):
    for msg in reversed(messages or []):
        if msg.get("role") == "assistant":
            return msg
    return None


def router_agent_node(state: AgentState) -> AgentState:
    """
    Router Agent: Evaluates user query and assigns appropriate intent and target agent.
    """
    query = state.get("query", "").strip()
    query_lower = query.lower()
    messages = state.get("messages", []) or []
    
    intent = "FAQ" # default fallback

    last_assistant = _last_assistant_message(messages)
    if _is_affirmative_followup(query_lower) and last_assistant and "salesagent" in (last_assistant.get("agent_name", "").lower()):
        intent = "COMPARISON"

    # Heuristic intent classification for fast, robust routing
    if intent != "COMPARISON" and any(k in query_lower for k in ["premium", "estimate", "cost", "price", "annual cost", "how much", "quote", "rate", "calculator"]):
        intent = "PREMIUM"
    elif any(k in query_lower for k in ["compare", "vs", "versus", "difference between", "which is better"]):
        intent = "COMPARISON"
    elif any(k in query_lower for k in ["recommend", "best policy", "suggest", "which plan should i buy", "suitable for me", "buy insurance", "sales"]):
        intent = "SALES"
    elif any(k in query_lower for k in ["claim", "eligible", "reimbursement", "cashless", "cataract", "hospitalized", "approval"]):
        intent = "CLAIM"
    elif any(k in query_lower for k in ["my age", "my profile", "i have diabetes", "hypertension", "smoke", "budget", "family floater"]):
        intent = "PROFILE"
    elif any(k in query_lower for k in ["cover", "exclusion", "waiting period", "room rent", "co-pay", "copay", "ped", "daycare", "maternity", "star health", "hdfc", "niva", "care supreme", "aspire", "activ"]):
        intent = "COVERAGE"
    elif any(k in query_lower for k in ["what is", "meaning of", "explain", "term", "no claim bonus", "ncb", "restoration", "tpa", "grace period"]):
        intent = "FAQ"

    # LLM enhancement if key available
    if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 10:
        try:
            from langchain_openai import ChatOpenAI
            llm_kwargs = {
                "model": settings.effective_model,
                "openai_api_key": settings.OPENAI_API_KEY,
                "temperature": 0
            }
            if settings.OPENAI_BASE_URL and len(settings.OPENAI_BASE_URL.strip()) > 5:
                llm_kwargs["base_url"] = settings.OPENAI_BASE_URL.strip()
            llm = ChatOpenAI(**llm_kwargs)
            prompt = (
                "Classify the following health insurance user request into EXACTLY ONE of these categories:\n"
                "- PREMIUM (asking for premium estimation, pricing, cost calculation, or annual quote)\n"
                "- PROFILE (user sharing or updating age, health conditions, budget, family details)\n"
                "- COVERAGE (queries about policy benefits, room rent, exclusions, waiting period, specific treatments)\n"
                "- COMPARISON (requesting side-by-side comparison of 2 or more insurance policies)\n"
                "- SALES (asking for best plan recommendations or buying advice based on profile)\n"
                "- CLAIM (asking about claim eligibility, approval likelihood, or reimbursement deductions)\n"
                "- FAQ (asking for definition of insurance terms or general insurance guidance)\n\n"
                f"User Request: {query}\n"
                "Return ONLY the category name."
            )
            res = llm.invoke(prompt)
            classified = res.content.strip().upper()
            if classified in ["PREMIUM", "PROFILE", "COVERAGE", "COMPARISON", "SALES", "CLAIM", "FAQ"]:
                intent = classified
        except Exception as e:
            logger.warning(f"Router LLM classification failed, using heuristic result '{intent}': {e}")

    state["intent"] = intent
    state["agent_used"] = f"RouterAgent -> {intent}Agent"
    logger.info(f"[RouterAgent] Classified query '{query[:40]}...' to intent: {intent}")
    return state

