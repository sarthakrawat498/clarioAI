import json
import logging
import re
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.models.policy import PolicyCatalog
from app.rag.seed_docs import discover_policy_documents, seed_policy_documents, _read_document_text

logger = logging.getLogger(__name__)


def _normalize_key(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip().lower()


def _read_text(file_path: str) -> str:
    return _read_document_text(file_path)



def _extract_first_match(text: str, patterns: List[str], default: str = "") -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()
    return default


def _extract_int(text: str, patterns: List[str], default: int) -> int:
    value = _extract_first_match(text, patterns, "")
    if not value:
        return default
    digits = re.sub(r"[^0-9]", "", value)
    return int(digits) if digits else default


def _extract_float(text: str, patterns: List[str], default: float) -> float:
    value = _extract_first_match(text, patterns, "")
    if not value:
        return default
    numeric = re.sub(r"[^0-9.]", "", value)
    try:
        return float(numeric)
    except ValueError:
        return default


def _build_catalog_payload(doc_info: Dict[str, str]) -> Dict[str, Any]:
    text = _read_text(doc_info["file_path"])

    room_rent_limit = _extract_first_match(
        text,
        [
            r"Room Rent Limit:\s*(.+)",
            r"Room Category:\s*(.+)",
            r"Room Rent:\s*(.+)",
        ],
        default="Single Private Room (No Capping)",
    )
    co_pay_percentage = _extract_float(
        text,
        [
            r"Co-?Payment(?: Clause)?:\s*(\d+(?:\.\d+)?)%",
            r"Co-?Pay(?:ment)?:\s*(\d+(?:\.\d+)?)%",
            r"(\d+(?:\.\d+)?)%\s*co-?payment",
        ],
        default=0.0,
    )
    ped_waiting_period_months = _extract_int(
        text,
        [
            r"PED(?: Waiting Period)?:\s*(\d+)\s*months",
            r"Pre-Existing Disease.*?(\d+)\s*months",
            r"waiting period.*?(\d+)\s*months.*?PED",
        ],
        default=36,
    )
    restoration_benefit = _extract_first_match(
        text,
        [
            r"Restore Benefit:\s*(.+)",
            r"Automatic Restore Benefit:\s*(.+)",
            r"Unlimited Automatic Recharge:\s*(.+)",
            r"ReAssure Forever Benefit:\s*(.+)",
        ],
        default="100% Instant Unlimited Restore",
    )
    no_claim_bonus = _extract_first_match(
        text,
        [
            r"No Claim Bonus.*?:\s*(.+)",
            r"Cumulative Bonus.*?:\s*(.+)",
            r"Lock the Premium.*?:\s*(.+)",
        ],
        default="50% per claim-free year up to 100%",
    )
    pre_hospitalization_days = _extract_int(
        text,
        [r"Pre-Hospitalization:\s*(\d+)\s*days", r"Pre-Hospitalization.*?(\d+)\s*days"],
        default=60,
    )
    post_hospitalization_days = _extract_int(
        text,
        [r"Post-Hospitalization:\s*(\d+)\s*days", r"Post-Hospitalization.*?(\d+)\s*days"],
        default=180,
    )
    network_hospitals_count = _extract_int(
        text,
        [
            r"([0-9,]+)\+?\s*cashless hospital",
            r"([0-9,]+)\+?\s*hospital partners",
            r"Network:\s*([0-9,]+)",
        ],
        default=10000,
    )
    claim_settlement_ratio = _extract_float(
        text,
        [r"([0-9]+(?:\.[0-9]+)?)%\s*claim settlement ratio", r"Claim Settlement Ratio:\s*([0-9]+(?:\.[0-9]+)?)%"],
        default=98.5,
    )

    highlights = []
    for candidate in [room_rent_limit, restoration_benefit, no_claim_bonus]:
        if candidate and candidate not in highlights:
            highlights.append(candidate)
    if ped_waiting_period_months:
        highlights.append(f"PED waiting period: {ped_waiting_period_months} months")
    if network_hospitals_count:
        highlights.append(f"Network size: {network_hospitals_count:,} hospitals")

    return {
        "insurer_name": doc_info["company"],
        "policy_name": doc_info["policy_name"],
        "plan_variant": "Standard",
        "room_rent_limit": room_rent_limit,
        "co_pay_percentage": co_pay_percentage,
        "ped_waiting_period_months": ped_waiting_period_months,
        "restoration_benefit": restoration_benefit,
        "no_claim_bonus": no_claim_bonus,
        "pre_hospitalization_days": pre_hospitalization_days,
        "post_hospitalization_days": post_hospitalization_days,
        "network_hospitals_count": network_hospitals_count,
        "claim_settlement_ratio": claim_settlement_ratio,
        "brochure_pdf_path": doc_info["file_path"],
        "description": f"Discovered from {doc_info['filename']}: {room_rent_limit}. {restoration_benefit}.",
        "key_highlights": json.dumps(highlights[:5]),
    }


def sync_policy_catalog(db: Session):
    """Synchronize the policy catalog table with discovered sample policy documents."""
    discovered = discover_policy_documents()
    if not discovered:
        seed_policy_documents()
        discovered = discover_policy_documents()

    existing_rows = db.query(PolicyCatalog).all()
    existing_index = {
        (_normalize_key(row.insurer_name), _normalize_key(row.policy_name)): row
        for row in existing_rows
    }

    touched = 0
    for doc_info in discovered:
        payload = _build_catalog_payload(doc_info)
        row_key = (_normalize_key(payload["insurer_name"]), _normalize_key(payload["policy_name"]))
        policy_row = existing_index.get(row_key)

        if policy_row is None:
            db.add(PolicyCatalog(**payload))
            touched += 1
            continue

        for field_name, value in payload.items():
            if value is not None and getattr(policy_row, field_name, None) != value:
                setattr(policy_row, field_name, value)
        touched += 1

    if touched:
        db.commit()
        logger.info("Policy catalog synchronized with discovered policy documents.")


def seed_policy_catalog(db: Session):
    """Backward-compatible bootstrap entry point for catalog initialization."""
    sync_policy_catalog(db)


def get_all_policies(db: Session, budget_annual_max: float | None = None) -> List[PolicyCatalog]:
    """Fetch policy catalogue, optionally restricted to affordable policies."""
    sync_policy_catalog(db)
    query = db.query(PolicyCatalog)
    if budget_annual_max is not None:
        query = query.filter(
            PolicyCatalog.base_annual_premium_estimate.isnot(None),
            PolicyCatalog.base_annual_premium_estimate <= budget_annual_max,
        )
    return query.order_by(PolicyCatalog.insurer_name.asc(), PolicyCatalog.policy_name.asc()).all()


def get_policy_by_id(db: Session, policy_id: int) -> PolicyCatalog:
    """Fetch policy by ID."""
    sync_policy_catalog(db)
    return db.query(PolicyCatalog).filter(PolicyCatalog.id == policy_id).first()


def serialize_policy_catalog(policies: List[PolicyCatalog]) -> List[Dict[str, Any]]:
    """Convert SQLAlchemy policy rows to plain dictionaries for agent payloads."""
    serialized = []
    for policy in policies:
        serialized.append({
            "policy_id": policy.id,
            "insurer_name": policy.insurer_name,
            "policy_name": policy.policy_name,
            "plan_variant": policy.plan_variant,
            "base_sum_insured_min": policy.base_sum_insured_min,
            "base_sum_insured_max": policy.base_sum_insured_max,
            "room_rent_limit": policy.room_rent_limit,
            "co_pay_percentage": policy.co_pay_percentage,
            "ped_waiting_period_months": policy.ped_waiting_period_months,
            "restoration_benefit": policy.restoration_benefit,
            "no_claim_bonus": policy.no_claim_bonus,
            "pre_hospitalization_days": policy.pre_hospitalization_days,
            "post_hospitalization_days": policy.post_hospitalization_days,
            "daycare_treatments_covered": policy.daycare_treatments_covered,
            "organ_donor_cover": policy.organ_donor_cover,
            "air_ambulance_cover": policy.air_ambulance_cover,
            "network_hospitals_count": policy.network_hospitals_count,
            "claim_settlement_ratio": policy.claim_settlement_ratio,
            "base_annual_premium_estimate": policy.base_annual_premium_estimate,
            "description": policy.description,
            "key_highlights": policy.key_highlights,
            "brochure_pdf_path": policy.brochure_pdf_path,
        })
    return serialized
