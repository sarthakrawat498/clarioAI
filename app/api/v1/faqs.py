from typing import List, Dict
from fastapi import APIRouter

router = APIRouter(prefix="/faqs", tags=["FAQs & Glossary Explainer"])

GLOSSARY_ITEMS = [
    {
        "term": "Pre-Existing Disease (PED)",
        "question": "What is a Pre-Existing Disease (PED)?",
        "category": "Terms",
        "explanation": "Any ailment, disease, or health condition diagnosed or treated by a physician within 48 months before purchasing the policy.",
        "answer": "Any ailment, disease, or health condition diagnosed or treated by a physician within 48 months before purchasing the policy."
    },
    {
        "term": "Restoration / Recharge Benefit",
        "question": "How does Restoration / Recharge Benefit work?",
        "category": "Benefits",
        "explanation": "Automatically reinstates 100% of your sum insured if it gets exhausted due to hospitalization during the policy year.",
        "answer": "Automatically reinstates 100% of your sum insured if it gets exhausted due to hospitalization during the policy year."
    },
    {
        "term": "No Claim Bonus (NCB)",
        "question": "What is a No Claim Bonus (NCB)?",
        "category": "Benefits",
        "explanation": "Bonus reward for every claim-free year that increases your sum insured (up to 500%) without increasing your premium.",
        "answer": "Bonus reward for every claim-free year that increases your sum insured (up to 500%) without increasing your premium."
    },
    {
        "term": "Room Rent Capping",
        "question": "What is Room Rent Capping?",
        "category": "Clauses",
        "explanation": "Limit set by insurers on daily room charge (e.g. 1% of Sum Insured). Staying in a higher category triggers proportionate deductions on doctor and surgeon fees.",
        "answer": "Limit set by insurers on daily room charge (e.g. 1% of Sum Insured). Staying in a higher category triggers proportionate deductions on doctor and surgeon fees."
    },
    {
        "term": "Co-Payment (Co-pay)",
        "question": "What is a Co-Payment (Co-pay) clause?",
        "category": "Clauses",
        "explanation": "A cost-sharing agreement where you pay a fixed percentage (10%-20%) of total bill out-of-pocket.",
        "answer": "A cost-sharing agreement where you pay a fixed percentage (10%-20%) of total bill out-of-pocket."
    },
    {
        "term": "Cashless Hospitalization",
        "question": "What is Cashless Hospitalization?",
        "category": "Claims",
        "explanation": "Direct settlement between insurer/TPA and network hospital where you do not need to pay upfront bills.",
        "answer": "Direct settlement between insurer/TPA and network hospital where you do not need to pay upfront bills."
    }
]

@router.get("", response_model=List[Dict[str, str]])
def get_faqs():
    """Retrieve health insurance glossary and frequently asked questions."""
    return GLOSSARY_ITEMS
