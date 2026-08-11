import logging
from typing import List, Dict, Any
from app.config import settings
from app.rag.vector_store import vector_store_manager
from app.agents.state import AgentState

logger = logging.getLogger(__name__)


def coverage_agent_node(state: AgentState) -> AgentState:
    """
    Coverage Agent: Queries vector store using metadata-aware retrieval,
    answers questions grounded strictly in retrieved documents with explicit citations.
    """
    query = state.get("query", "")
    filter_company = state.get("filter_company")
    filter_policy = state.get("filter_policy")

    # Perform ChromaDB RAG Search
    retrieved = vector_store_manager.query(
        query_text=query,
        n_results=4,
        company_filter=filter_company,
        policy_filter=filter_policy
    )

    state["retrieved_docs"] = retrieved
    sources = []
    
    if not retrieved:
        state["final_response"] = (
            "⚠️ Insufficient Document Context: I could not find any explicit policy clause in the indexed "
            "health insurance documents regarding your query. To prevent misinformation or hallucinations, "
            "please verify directly with the official policy prospectus or refine your question."
        )
        state["sources"] = []
        state["agent_used"] = "CoverageAgent (RAG Grounded)"
        return state

    # Build context string & formatted source citations
    context_blocks = []
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

    # Use LLM or deterministic fallback grounded generator
    answer = ""
    if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 10:
        try:
            from langchain_openai import ChatOpenAI
            llm_kwargs = {
                "model": settings.effective_model,
                "openai_api_key": settings.OPENAI_API_KEY,
                "temperature": 0.1
            }
            if settings.OPENAI_BASE_URL and len(settings.OPENAI_BASE_URL.strip()) > 5:
                llm_kwargs["base_url"] = settings.OPENAI_BASE_URL.strip()
            llm = ChatOpenAI(**llm_kwargs)
            prompt = (
                "You are an expert Health Insurance RAG Assistant. Your job is to answer the user's query STRICTLY "
                "based on the provided policy documents below. DO NOT make up information or use outside assumptions.\n"
                "For every key statement or clause you present, cite the exact source using format [Company: X, Policy: Y, Page: Z].\n\n"
                f"--- RETRIEVED POLICY DOCUMENTS ---\n{combined_context}\n-----------------------------------\n\n"
                f"User Question: {query}\n\n"
                "Provide a detailed, professional, structured answer with markdown bullet points and exact citations."
            )
            res = llm.invoke(prompt)
            answer = res.content.strip()
        except Exception as e:
            logger.warning(f"Coverage Agent LLM call failed: {e}. Using deterministic synthesis.")
            answer = ""

    if not answer:
        # Deterministic grounded fallback synthesis
        lines = [
            f"📄 Policy Coverage Details & Analysis",
            f"Based strictly on the retrieved health insurance policy documents, here are the clauses relevant to your question:\n"
        ]
        for doc in retrieved:
            lines.append(f"{doc['company']} - {doc['policy_name']} (Page {doc['page']})")
            lines.append(f"> {doc['content']}")
            lines.append(f"Citation: `[Company: {doc['company']}, Policy: {doc['policy_name']}, Page: {doc['page']}]`\n")
        
        answer = "\n".join(lines)

    state["final_response"] = answer
    state["agent_used"] = "CoverageAgent (RAG Grounded)"
    return state
