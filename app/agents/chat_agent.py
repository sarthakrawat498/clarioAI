import logging
from app.config import settings
from app.agents.state import AgentState

logger = logging.getLogger(__name__)

FAQ_KNOWLEDGE_BASE = {
    "ped": "Pre-existing Disease (PED) refers to any health condition, ailment, or injury that was diagnosed or treated within 48 months prior to purchasing the health insurance policy. Standard waiting periods range from 12 to 36 months.",
    "restoration": "Restoration or Recharge Benefit automatically reinstates 100% of your sum insured if it gets exhausted due to hospitalization during a policy year. Unlimited restoration allows multiple reinstatements.",
    "ncb": "No Claim Bonus (Cumulative Bonus) rewards policyholders for claim-free years by increasing the base sum insured (from 20% to 500%) without increasing the premium.",
    "co-pay": "Co-payment is a cost-sharing clause where the policyholder agrees to pay a fixed percentage (e.g. 10% or 20%) of the medical bill out-of-pocket, while the insurer pays the remaining percentage.",
    "room rent": "Room rent capping limits the daily room expense covered by insurance. If you choose a room above your capping limit (e.g., opting for Suite when Single Private is allowed), insurers apply proportionate deductions to all doctor and surgery charges.",
    "tpa": "Third Party Administrator (TPA) is an organization licensed by IRDAI to process claims and facilitate cashless hospitalization between the hospital and the insurance company."
}


def chat_agent_node(state: AgentState) -> AgentState:
    """
    Chat Agent: Answers general health insurance questions, terminology, and FAQs.
    """
    query = state.get("query", "").lower()
    
    answer = ""
    # Check knowledge base dictionary
    for key, desc in FAQ_KNOWLEDGE_BASE.items():
        if key in query:
            answer = f"Insurance Term Explainer: {key.upper()}\n\n{desc}\n\n*Feel free to ask about specific policies, run a claim check, or compare plans!"
            break

    if not answer and settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 10:
        try:
            from langchain_openai import ChatOpenAI
            llm_kwargs = {
                "model": settings.effective_model,
                "openai_api_key": settings.OPENAI_API_KEY,
                "temperature": 0.3
            }
            if settings.OPENAI_BASE_URL and len(settings.OPENAI_BASE_URL.strip()) > 5:
                llm_kwargs["base_url"] = settings.OPENAI_BASE_URL.strip()
            llm = ChatOpenAI(**llm_kwargs)
            prompt = (
                "You are an empathetic, expert Indian Health Insurance Assistant. Answer the user's general insurance question "
                "clearly, accurately, and concisely with markdown formatting.\n\n"
                f"User Question: {state.get('query')}"
            )
            res = llm.invoke(prompt)
            answer = res.content.strip()
        except Exception as e:
            logger.warning(f"ChatAgent LLM call failed: {e}")
            answer = ""

    if not answer:
        answer = (
            "Health Insurance AI Assistant\n"
            "I am here to guide you through your health insurance decisions! You can ask me to:\n"
            "1. Analyze Coverage: Check room rent limits, co-pay, or waiting periods for HDFC Optima Secure, Star Health, Niva Bupa, or Care Supreme.\n"
            "2. Compare Policies: View a side-by-side matrix of key features.\n"
            "3. Get Tailored Recommendations: Score plans matching your age, family size, and pre-existing conditions.\n"
            "4. Check Claim Eligibility: Estimate approval percentage and out-of-pocket expenses for a treatment."
        )

    state["final_response"] = answer
    state["agent_used"] = "ChatAgent"
    return state
