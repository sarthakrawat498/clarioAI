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


from app.config import settings
from app.rag.vector_store import vector_store_manager
from app.agents.state import AgentState

logger = logging.getLogger(__name__)


def chat_agent_node(state: AgentState) -> AgentState:
    """
    Chat Agent: Answers general health insurance questions, terminology, and FAQs using PDF RAG context & LLM.
    """
    query = state.get("query", "").strip()

    # RAG Vector Search for relevant policy chunks
    retrieved = vector_store_manager.query(query_text=query, n_results=4)
    context_blocks = []
    sources = []
    for doc in retrieved:
        citation_str = f"[Company: {doc['company']}, Policy: {doc['policy_name']}, Page: {doc['page']}]"
        context_blocks.append(f"Source {citation_str}:\n{doc['content']}")
        sources.append({
            "company": doc["company"],
            "policy_name": doc["policy_name"],
            "page": doc["page"],
            "chunk_id": doc["chunk_id"],
            "snippet": doc["content"][:200] + "...",
            "score": doc["score"]
        })

    combined_context = "\n\n".join(context_blocks)
    state["sources"] = sources

    answer = ""
    if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 10:
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
                "You are an empathetic, highly knowledgeable AI Health Insurance Advisor. "
                "Answer the user's health insurance question clearly, accurately, and thoroughly for a client-ready, production-level experience.\n\n"
                f"--- RETRIEVED PDF POLICY CONTEXT ---\n{combined_context if combined_context else 'No specific policy chunk retrieved.'}\n-----------------------------------\n\n"
                f"User Question: {query}\n\n"
                "CRITICAL FORMATTING INSTRUCTIONS FOR PRODUCTION VISUALIZATION:\n"
                "- DO NOT use raw hash header symbols (like #, ##, ###). Use clean bold section titles (e.g. **Coverage Summary**).\n"
                "- DO NOT include bracketed citations, page numbers, or policy citations (such as [Company: X, Policy: Y, Page: Z]). Present all information directly in natural, professional language.\n"
                "- Structure your response using clean paragraphs, bullet points (- item), and plain markdown tables where applicable.\n"
                "- Provide a direct, well-structured answer with bold key terms for readability."

            )
            res = llm.invoke(prompt)
            answer = res.content.strip()
        except Exception as e:
            logger.warning(f"ChatAgent LLM call failed: {e}")
            answer = ""


    if not answer:
        answer = (
            f"### 💡 Health Insurance Assistant\n\n"
            f"Here is information regarding your query: **\"{query}\"**\n\n"
            "Health insurance plans differ in their features, coverage terms, room rent limits, and waiting periods. "
            "You can ask me to compare specific policies (Niva Bupa Aspire, Care Supreme, HDFC Optima Secure, Aditya Birla Activ One) "
            "or check custom claim scenarios!"
        )

    state["final_response"] = answer
    state["agent_used"] = "ChatAgent (RAG Grounded)"
    return state

