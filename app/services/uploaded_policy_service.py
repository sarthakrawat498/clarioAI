import io
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from fastapi import UploadFile
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.models.uploaded_policy import UploadedPolicySnapshot

logger = logging.getLogger(__name__)


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _extract_lines(text: str) -> List[str]:
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


def _extract_line_value(text: str, keywords: List[str]) -> str:
    lines = _extract_lines(text)
    for index, line in enumerate(lines):
        normalized = re.sub(r"^[\s\-•*\.]+", "", line).strip()
        lowered = normalized.lower()
        if not any(keyword in lowered for keyword in keywords):
            continue

        inline_value = re.search(r"(?:[:\-]|—)\s*(.+)$", normalized)
        if inline_value and _clean_text(inline_value.group(1)):
            return _clean_text(inline_value.group(1))

        table_cells = [cell.strip() for cell in re.split(r"\t+|\s{2,}", normalized) if cell.strip()]
        if len(table_cells) >= 2:
            first_cell = table_cells[0].lower()
            if any(keyword in first_cell for keyword in keywords):
                return _clean_text(" ".join(table_cells[1:]))

        if index + 1 < len(lines):
            next_line = re.sub(r"^[\s\-•*\.]+", "", lines[index + 1]).strip()
            if next_line and not any(keyword in next_line.lower() for keyword in keywords):
                return _clean_text(next_line)

        return _clean_text(normalized)
    return ""


def _extract_field_value(text: str, patterns: List[str], keywords: List[str]) -> str:
    value = _extract_first_match(text, patterns)
    if value:
        return value
    return _extract_line_value(text, keywords)


def _parse_money_value(raw_value: str) -> Optional[float]:
    if not raw_value:
        return None

    cleaned = raw_value.replace(",", "").replace("₹", " ").replace("Rs.", " ").replace("Rs", " ")
    numeric_match = re.search(r"([0-9]+(?:\.[0-9]+)?)", cleaned)
    if not numeric_match:
        return None

    amount = float(numeric_match.group(1))
    lowered = cleaned.lower()

    if any(unit in lowered for unit in ["crore", "crores", "cr"]):
        return amount * 10000000.0
    if any(unit in lowered for unit in ["lakh", "lakhs", "lac", "lacs", "lak"]):
        return amount * 100000.0
    if any(unit in lowered for unit in ["thousand", "k"]):
        return amount * 1000.0

    return amount


def _extract_first_match(text: str, patterns: List[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return _clean_text(match.group(1))
    return ""


def _extract_policy_name(text: str, file_name: str) -> str:
    candidate = _extract_first_match(
        text,
        [
            r"Policy Name[:\-]\s*(.+)",
            r"Policy(?:\s+Wordings?|\s+Prospectus|\s+Guidelines?)[:\-]\s*(.+)",
            r"Plan Name[:\-]\s*(.+)",
            r"Plan[:\-]\s*(.+)",
        ],
    )
    if candidate:
        return candidate

    stem = os.path.splitext(os.path.basename(file_name or "policy_document"))[0]
    stem = stem.replace("---", " ").replace("_", " ").replace("-", " ")
    return _clean_text(stem.title())


def _extract_amount(text: str, patterns: List[str]) -> Optional[float]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            amount = _parse_money_value(match.group(1))
            if amount is not None:
                return amount
    return None


def _extract_percentage(text: str, patterns: List[str]) -> Optional[float]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            raw_value = _clean_text(match.group(1)).replace("%", "")
            numeric_match = re.search(r"([0-9]+(?:\.[0-9]+)?)", raw_value)
            if numeric_match:
                try:
                    return float(numeric_match.group(1))
                except ValueError:
                    continue
    return None


def _extract_integer(text: str, patterns: List[str]) -> Optional[int]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            numeric_match = re.search(r"([0-9]+)", _clean_text(match.group(1)))
            if numeric_match:
                try:
                    return int(numeric_match.group(1))
                except ValueError:
                    continue
    return None


def _extract_benefits(text: str) -> List[str]:
    benefits: List[str] = []
    keywords = re.compile(r"benefit|cover|coverage|restore|recharge|bonus|cashless|room rent|daycare|copay|co-pay|waiting period|sum insured", re.IGNORECASE)

    for line in _extract_lines(text):
        normalized = re.sub(r"^[\s\-•*\.]+", "", line).strip()
        if not normalized or len(normalized) > 220:
            continue
        if keywords.search(normalized) and normalized not in benefits:
            benefits.append(normalized)
        if len(benefits) >= 8:
            break

    return benefits


def _first_non_empty(*values: str) -> str:
    for value in values:
        if value:
            return value
    return ""


def _extract_structured_summary(text: str) -> Dict[str, Any]:
    benefits = _extract_benefits(text)
    room_rent = _first_non_empty(
        _extract_field_value(
            text,
            [
                r"Room Rent(?: Category| Limit)?[:\-]\s*([^\n]+)",
                r"Room Category[:\-]\s*([^\n]+)",
                r"Room rent[:\-]\s*([^\n]+)",
            ],
            ["room rent", "room category", "room-rent"],
        ),
        next(
            (
                line
                for line in benefits
                if "room rent" in line.lower()
                or ("room" in line.lower() and "capping" in line.lower())
            ),
            "",
        )
    )

    co_pay_percentage = _extract_percentage(
        _extract_field_value(
            text,
            [
                r"Co[- ]?Pay(?:ment)?[:\-]\s*([^\n]+)",
                r"Copay(?:ment)?[:\-]\s*([^\n]+)",
            ],
            ["co-pay", "copay", "co pay"],
        ),
        [r"([0-9]+(?:\.[0-9]+)?)"],
    )

    ped_waiting_period_months = _extract_integer(
        _extract_field_value(
            text,
            [
                r"PED Waiting Period[:\-]\s*([^\n]+)",
                r"Pre[- ]Existing Disease Waiting Period[:\-]\s*([^\n]+)",
                r"Waiting Period[:\-]\s*([^\n]+)",
            ],
            ["ped waiting", "pre-existing disease waiting", "waiting period"],
        ),
        [r"([0-9]+)"],
    )

    restoration_benefit = _first_non_empty(
        _extract_field_value(
            text,
            [
                r"Restoration Benefit[:\-]\s*([^\n]+)",
                r"Restore(?: Benefit)?[:\-]\s*([^\n]+)",
                r"Recharge[:\-]\s*([^\n]+)",
            ],
            ["restoration", "restore", "recharge"],
        ),
        next((line for line in benefits if "restore" in line.lower() or "recharge" in line.lower()), ""),
    )

    no_claim_bonus = _first_non_empty(
        _extract_field_value(
            text,
            [
                r"No Claim Bonus(?: \(NCB\))?[:\-]\s*([^\n]+)",
                r"NCB[:\-]\s*([^\n]+)",
                r"Bonus[:\-]\s*([^\n]+)",
            ],
            ["no claim bonus", "ncb", "bonus"],
        ),
        next((line for line in benefits if "bonus" in line.lower()), ""),
    )

    pre_hospitalization_days = _extract_integer(
        _extract_field_value(
            text,
            [
                r"Pre[- ]Hospitalization[:\-]\s*([^\n]+)",
                r"Pre[- ]Hospitalisation[:\-]\s*([^\n]+)",
            ],
            ["pre hospitalization", "pre-hospitalization", "pre hospitalization days"],
        ),
        [r"([0-9]+)"],
    )

    post_hospitalization_days = _extract_integer(
        _extract_field_value(
            text,
            [
                r"Post[- ]Hospitalization[:\-]\s*([^\n]+)",
                r"Post[- ]Hospitalisation[:\-]\s*([^\n]+)",
            ],
            ["post hospitalization", "post-hospitalization", "post hospitalization days"],
        ),
        [r"([0-9]+)"],
    )

    claim_settlement_ratio = _extract_percentage(
        _extract_field_value(
            text,
            [
                r"Claim Settlement Ratio[:\-]\s*([^\n]+)",
                r"Settlement Ratio[:\-]\s*([^\n]+)",
            ],
            ["claim settlement ratio", "settlement ratio"],
        ),
        [r"([0-9]+(?:\.[0-9]+)?)"],
    )

    network_hospitals_count = _extract_integer(
        _extract_field_value(
            text,
            [
                r"Network Hospitals(?: Count)?[:\-]\s*([^\n]+)",
                r"Hospitals?:\s*([^\n]+)",
            ],
            ["network hospitals", "hospital network", "cashless network"],
        ),
        [r"([0-9]+)"],
    )

    daycare_treatments_covered = None
    air_ambulance_cover = None
    lower_text = text.lower()
    if "daycare" in lower_text:
        daycare_treatments_covered = not any(token in lower_text for token in ["not covered", "excluded", "no daycare"])
    if "air ambulance" in lower_text:
        air_ambulance_cover = not any(token in lower_text for token in ["not covered", "excluded", "no air ambulance"])

    return {
        "benefits": benefits,
        "room_rent_limit": room_rent or None,
        "co_pay_percentage": co_pay_percentage,
        "ped_waiting_period_months": ped_waiting_period_months,
        "restoration_benefit": restoration_benefit or None,
        "no_claim_bonus": no_claim_bonus or None,
        "pre_hospitalization_days": pre_hospitalization_days,
        "post_hospitalization_days": post_hospitalization_days,
        "daycare_treatments_covered": daycare_treatments_covered,
        "air_ambulance_cover": air_ambulance_cover,
        "claim_settlement_ratio": claim_settlement_ratio,
        "network_hospitals_count": network_hospitals_count,
    }


def extract_uploaded_policy_metadata(file_name: str, file_bytes: bytes, content_type: Optional[str] = None) -> Dict[str, Any]:
    """Extract structured policy metadata from an uploaded PDF or text document."""
    text = ""
    is_pdf = (file_name or "").lower().endswith(".pdf") or (content_type or "").lower() == "application/pdf"

    if is_pdf:
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n\n".join(pages)
        except Exception as exc:
            logger.warning("Failed to parse uploaded PDF '%s': %s", file_name, exc)

    if not text.strip():
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1", errors="ignore")

    policy_name = _extract_policy_name(text, file_name)
    sum_assured_amount = _extract_amount(
        text,
        [
            r"Sum Assured(?: Amount)?[:\-]?\s*([^\n]+)",
            r"Sum Insured(?: Amount)?[:\-]?\s*([^\n]+)",
            r"Base Sum Insured(?: Amount)?[:\-]?\s*([^\n]+)",
            r"Coverage Amount[:\-]?\s*([^\n]+)",
        ],
    )
    premium_amount = _extract_amount(
        text,
        [
            r"Annual Premium(?: Amount)?[:\-]?\s*([^\n]+)",
            r"Policy Premium(?: Amount)?[:\-]?\s*([^\n]+)",
            r"Premium(?: Amount)?[:\-]?\s*([^\n]+)",
        ],
    )
    structured_summary = _extract_structured_summary(text)

    return {
        "source_file_name": file_name,
        "policy_name": policy_name,
        "sum_assured_amount": sum_assured_amount,
        "premium_amount": premium_amount,
        "benefits": structured_summary.get("benefits", []),
        **structured_summary,
        "raw_excerpt": _clean_text(text[:2000]),
    }


def save_uploaded_policy_snapshot(
    db: Session,
    user_id: int,
    chat_session_id: Optional[int],
    file_name: str,
    extracted: Dict[str, Any],
) -> UploadedPolicySnapshot:
    snapshot = UploadedPolicySnapshot(
        user_id=user_id,
        chat_session_id=chat_session_id,
        source_file_name=file_name,
        policy_name=extracted.get("policy_name"),
        sum_assured_amount=extracted.get("sum_assured_amount"),
        premium_amount=extracted.get("premium_amount"),
        benefits_json=json.dumps(extracted.get("benefits", [])),
        extracted_json=json.dumps(extracted),
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_latest_uploaded_policy_snapshot(
    db: Session,
    user_id: int,
    chat_session_id: Optional[int] = None,
) -> Optional[UploadedPolicySnapshot]:
    query = db.query(UploadedPolicySnapshot).filter(UploadedPolicySnapshot.user_id == user_id)
    if chat_session_id is not None:
        query = query.filter(UploadedPolicySnapshot.chat_session_id == chat_session_id)
    return query.order_by(UploadedPolicySnapshot.created_at.desc()).first()


def build_uploaded_policy_context(snapshot: UploadedPolicySnapshot, user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    user_profile = user_profile or {}
    extracted = {}
    if snapshot.extracted_json:
        try:
            extracted = json.loads(snapshot.extracted_json)
        except Exception:
            extracted = {}

    benefits = []
    if snapshot.benefits_json:
        try:
            benefits = json.loads(snapshot.benefits_json)
        except Exception:
            benefits = []

    uploaded_premium = snapshot.premium_amount
    uploaded_sum_assured = snapshot.sum_assured_amount
    target_sum_insured = uploaded_sum_assured or user_profile.get("sum_insured_preference")
    effective_budget = uploaded_premium or user_profile.get("budget_annual_max")

    premium_floor = uploaded_premium * 0.8 if uploaded_premium else None
    premium_ceiling = uploaded_premium * 1.2 if uploaded_premium else None

    return {
        "source_file_name": snapshot.source_file_name,
        "policy_name": snapshot.policy_name,
        "uploaded_sum_assured": uploaded_sum_assured,
        "uploaded_premium": uploaded_premium,
        "effective_budget": effective_budget,
        "premium_floor": premium_floor,
        "premium_ceiling": premium_ceiling,
        "target_sum_insured": target_sum_insured,
        "use_uploaded_policy_as_primary": bool(uploaded_premium or uploaded_sum_assured),
        "benefits": benefits,
        "extracted_summary": extracted,
    }
