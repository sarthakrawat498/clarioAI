from typing import List, Dict, Any, Optional, Annotated
from typing_extensions import TypedDict
import operator

class AgentState(TypedDict):
    """LangGraph State representation across multi-agent graph nodes."""
    messages: List[Dict[str, str]] # List of {"role": "user"|"assistant", "content": "..."}
    user_profile: Dict[str, Any] # Profile parameters (age, city, ped, budget, etc.)
    age: Optional[int]
    gender: Optional[str]
    city: Optional[str]
    coverage_type: Optional[str]
    sum_insured_preference: Optional[float]
    budget_annual_max: Optional[float]
    pre_existing_diseases: Optional[List[str]]
    intent: str # 'PROFILE', 'COVERAGE', 'COMPARISON', 'SALES', 'CLAIM', 'FAQ'
    query: str # Latest user message
    
    # RAG & Domain payloads
    retrieved_docs: List[Dict[str, Any]]
    sources: List[Dict[str, Any]]
    
    # Response payloads
    final_response: str
    agent_used: str
    recommended_policies: Optional[List[Dict[str, Any]]]
    comparison_table: Optional[Dict[str, Any]]
    policy_catalog: Optional[List[Dict[str, Any]]]
    uploaded_policy_baseline: Optional[Dict[str, Any]]
    filter_company: Optional[str]
    filter_policy: Optional[str]
    claim_amount: Optional[float]
    compare_policy_ids: Optional[List[int]]
