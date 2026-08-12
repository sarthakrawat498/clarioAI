import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

SAMPLE_DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "sample_policies")

COMPANY_ALIASES = {
    "hdfc ergo": "HDFC ERGO",
    "niva bupa": "Niva Bupa",
    "nbh": "Niva Bupa",
    "star health": "Star Health",
    "care health": "Care Health",
    "care": "Care Health",
    "aditya birla": "Aditya Birla",
}

POLICY_ALIASES = {
    "optima secure": "Optima Secure",
    "optima restore": "Optima Restore",
    "reassure 2.0": "ReAssure 2.0",
    "reassure 2": "ReAssure 2.0",
    "care supreme": "Care Supreme",
    "aspire": "Aspire",
    "activ one": "Activ One",
    "activ health": "Activ Health",
}


def _read_document_text(file_path: str) -> str:
    if file_path.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            pages_text = []
            for p in reader.pages[:10]:
                txt = p.extract_text()
                if txt:
                    pages_text.append(txt)
            return "\n".join(pages_text)
        except Exception as e:
            print(f"[SeedDocs] Warning reading PDF {file_path}: {e}")
            return ""
    else:
        with open(file_path, "r", encoding="utf-8") as file_handle:
            return file_handle.read()


def _canonical_name(value: str, aliases: Dict[str, str]) -> str:
    lowered = value.lower()
    for needle, canonical in aliases.items():
        if needle in lowered:
            return canonical
    return " ".join(part.capitalize() for part in re.split(r"[\s_\-]+", value.strip()) if part)


def _extract_company(text: str, filename: str) -> str:
    for line in [line.strip() for line in text.splitlines() if line.strip()][:25]:
        company = _canonical_name(line, COMPANY_ALIASES)
        if company in COMPANY_ALIASES.values():
            return company
    stem = Path(filename).stem.replace("---", " ").replace("_", " ").replace("-", " ")
    return _canonical_name(stem, COMPANY_ALIASES)


def _extract_policy_name(text: str, filename: str) -> str:
    patterns = [
        r"Product\s+Name\s*:\s*([A-Za-z0-9 .&/()-]+)",
        r"POLICY\s+(?:WORDINGS|PROSPECTUS|GUIDELINES|WORDING)\s*:\s*([A-Z0-9 .&/()-]+?)(?:\s+PLAN|\s*\(|\n)",
        r"\b(OPTIMA\s+SECURE|OPTIMA\s+RESTORE|REASSURE\s+2(?:\.0)?|CARE\s+SUPREME|ASPIRE|ACTIV\s+ONE|ACTIV\s+HEALTH)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return _canonical_name(match.group(1), POLICY_ALIASES)

    stem = Path(filename).stem.lower().replace("---", " ").replace("_", " ").replace("-", " ")
    return _canonical_name(stem, POLICY_ALIASES)


def discover_policy_documents() -> List[Dict[str, str]]:
    """Discover policy files (PDF or TXT) from the sample policy directory."""
    if not os.path.isdir(SAMPLE_DOCS_DIR):
        return []

    discovered: List[Dict[str, str]] = []
    seen = set()

    for filename in sorted(os.listdir(SAMPLE_DOCS_DIR)):
        if not (filename.lower().endswith(".txt") or filename.lower().endswith(".pdf")):
            continue

        file_path = os.path.join(SAMPLE_DOCS_DIR, filename)
        if not os.path.isfile(file_path):
            continue

        text = _read_document_text(file_path)
        company = _extract_company(text, filename)
        policy_name = _extract_policy_name(text, filename)

        # Special casing if filename is Aspire -> Niva Bupa
        if "aspire" in filename.lower() and company not in COMPANY_ALIASES.values():
            company = "Niva Bupa"

        dedupe_key = (company.lower(), policy_name.lower())
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        first_line = text.splitlines()[0].strip() if text.splitlines() else filename

        discovered.append({
            "company": company,
            "policy_name": policy_name,
            "filename": filename,
            "file_path": file_path,
            "description": first_line[:200] if len(first_line) > 200 else first_line,
        })

    return discovered


POLICY_DOCUMENTS = [
    {
        "company": "HDFC ERGO",
        "policy_name": "Optima Secure",
        "filename": "hdfc_ergo_optima_secure.txt",
        "pages": [
            """HDFC ERGO GENERAL INSURANCE COMPANY LIMITED
POLICY WORDINGS: OPTIMA SECURE PLAN (Page 1)

SECTION 1: PRODUCT HIGHLIGHTS & KEY BENEFITS
1.1 Secure Benefit: Automatically doubles your base sum insured from Day 1 at no extra cost. For example, a 10 Lakhs policy becomes 20 Lakhs base coverage instantly.
1.2 Plus Benefit: Increases base sum insured by 50% after Year 1 and 100% after Year 2 regardless of claims made.
1.3 Restore Benefit: 100% automatic restore benefit triggered for any illness, related or unrelated, once per policy year.
1.4 Protect Benefit: Covers zero-deduction consumable expenses such as gloves, masks, PPE kits, hand sanitizers during hospitalization.

SECTION 2: HOSPITALIZATION & ROOM RENT
2.1 Room Rent Limit: No capping on room rent. Any room category up to Single Private Air-Conditioned Room is 100% covered.
2.2 ICU Charges: No capping on Intensive Care Unit (ICU) charges.
2.3 Co-Pay: 0% co-payment for all age groups up to 65 years. No zonal co-payment applies if treated anywhere in India.
2.4 Pre-Hospitalization: Expenses covered up to 60 days prior to hospital admission.
2.5 Post-Hospitalization: Expenses covered up to 180 days after discharge from hospital.""",

            """HDFC ERGO GENERAL INSURANCE COMPANY LIMITED
POLICY WORDINGS: OPTIMA SECURE PLAN (Page 2)

SECTION 3: WAITING PERIODS & PRE-EXISTING DISEASES
3.1 Initial Waiting Period: 30 days initial waiting period for all illnesses except accidental injuries.
3.2 Specific Illness Waiting Period: 24 months waiting period for Cataract, Hernia, Hysterectomy, Joint Replacement, Kidney Stones, Sinusitis.
3.3 Pre-Existing Diseases (PED): 36 months continuous coverage waiting period for pre-existing conditions declared at inception (e.g., Diabetes, Hypertension, Asthma).
3.4 Optional PED Reduction Rider: Can reduce PED waiting period from 36 months to 12 months by paying additional premium loading.

SECTION 4: DAY CARE & ADVANCED TREATMENTS
4.1 Daycare Treatments: All daycare procedures requiring less than 24 hours hospitalization due to technological advancement are covered up to full sum insured.
4.2 Robotic Surgery & Modern Treatments: Covers Robotic Surgeries, Stem Cell Therapy, Uterine Artery Embolization, Vaporisation of Prostate up to 100% sum insured.
4.3 Air Ambulance: Covered up to INR 5,00,000 per hospitalization.
4.4 Organ Donor Expense: Inpatient hospitalization expenses of organ donor covered up to base sum insured.

SECTION 5: EXCLUSIONS & CLAIM PROCEDURE
5.1 Exclusions: Cosmetic surgery, intentional self-injury, alcoholism/substance abuse, dental surgery unless arising from accident, weight loss/bariatric surgery unless medically required.
5.2 Cashless Claim Notice: Network hospital cashless requests must be submitted at least 48 hours prior to planned admission, or within 24 hours of emergency admission."""
        ]
    },
    {
        "company": "Star Health",
        "policy_name": "Optima Restore",
        "filename": "star_health_optima_restore.txt",
        "pages": [
            """STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED
POLICY PROSPECTUS: STAR OPTIMA RESTORE (Page 1)

SECTION 1: CORE BENEFIT SUMMARY
1.1 Automatic Restore Benefit: If basic sum insured is partially or fully exhausted, 100% of basic sum insured is automatically restored once in a policy year. Restored amount can be used for subsequent hospitalizations.
1.2 Cumulative Bonus (NCB): 20% increase in sum insured for every claim-free year up to a maximum of 100% sum insured. Bonus is reduced by 20% in case of claim.
1.3 Health Checkup: Free annual health checkup after every claim-free year for all insured members up to INR 5,000 limit.

SECTION 2: ROOM RENT & HOSPITAL CHARGES
2.1 Room Rent Category: Covered up to Single Private AC Room. If insured chooses a higher category (e.g. Suite), proportionate deductions apply to nursing, doctor fees, and surgeon charges.
2.2 Co-Payment Clause: 10% co-payment applicable if the insured person enters policy for the first time above 61 years of age. 0% co-payment for age below 60.
2.3 Pre-Hospitalization: 60 days covered prior to admission date.
2.4 Post-Hospitalization: 90 days covered post hospital discharge.""",

            """STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED
POLICY PROSPECTUS: STAR OPTIMA RESTORE (Page 2)

SECTION 3: WAITING PERIODS & SPECIFIC COVERAGES
3.1 Initial Waiting Period: 30 days for non-accidental illnesses.
3.2 Pre-Existing Disease (PED) Waiting Period: 48 months (4 years) of continuous coverage required before PED claims are payable.
3.3 Specific Surgical Waiting Period: 24 months for Cataract, Joint Replacements, Calculus diseases, Piles, Fistula, Hydrocele.
3.4 Cataract Sub-Limit: Cataract surgery limited to INR 40,000 per eye or INR 60,000 per policy year.

SECTION 4: EMERGENCY & ADD-ON COVERS
4.1 Road Ambulance: Covered up to INR 3,000 per hospital admission in network/non-network hospital.
4.2 Air Ambulance: Covered up to INR 2,50,000 per policy year upon medical recommendation.
4.3 Domiciliary Hospitalization: Covered if treatment exceeds 3 days and patient cannot be moved to hospital due to critical condition or room unavailability.
4.4 Exclusions: Obesity treatments, IVF/fertility treatments, psychiatric disorders (unless inpatient hospitalization required for >5 days), unproven treatments."""
        ]
    },
    {
        "company": "Care Health Insurance",
        "policy_name": "Care Supreme",
        "filename": "care_health_supreme.txt",
        "pages": [
            """CARE HEALTH INSURANCE LIMITED
POLICY WORDINGS: CARE SUPREME PLAN (Page 1)

SECTION 1: PRODUCT OVERVIEW & UNLIMITED BENEFITS
1.1 Unlimited Automatic Recharge: Restores 100% of sum insured unlimited times per year for any illness, including same illness repeat claims.
1.2 Cumulative Bonus Super: 50% increase in base sum insured per claim-free year up to maximum 500% (5x base sum insured).
1.3 E-Consultations: Unlimited online general physician tele-consultations through Care Health Mobile App.

SECTION 2: ROOM RENT & ELIGIBILITY
2.1 Room Rent Limit: Absolutely No Room Rent Capping! Insured can choose any room category including Deluxe/Suite without proportionate deduction penalties.
2.2 Co-Pay: 0% Co-payment across all network hospitals in India.
2.3 Pre-Hospitalization: 60 days before hospital admission.
2.4 Post-Hospitalization: 180 days post hospital discharge.
2.5 Daycare Procedures: All daycare treatments covered up to full sum insured.""",

            """CARE HEALTH INSURANCE LIMITED
POLICY WORDINGS: CARE SUPREME PLAN (Page 2)

SECTION 3: WAITING PERIODS & PRE-EXISTING DISEASES
3.1 Initial Waiting Period: 30 days from policy inception.
3.2 PED Waiting Period: Standard 36 months for pre-existing diseases. Can be modified to 12 or 24 months with Instant PED Add-On Cover.
3.3 Specific Diseases: 24 months waiting period for Cataract, ENT disorders, Joint replacements, Gynaecological surgeries.

SECTION 4: ADVANCED RIDERS & CLAIMS
4.1 Instant Cover Rider: Covers Asthma, Diabetes, Hypertension, Hyperlipidemia after 30 days of policy purchase.
4.2 Claim Settlement: 95.2% Claim Settlement Ratio with average turn-around time (TAT) of 2 hours for cashless approvals.
4.3 Maternity & Newborn Rider: Optional add-on covering delivery expenses up to INR 1,00,000 and newborn baby vaccination up to 1 year."""
        ]
    },
    {
        "company": "Niva Bupa",
        "policy_name": "ReAssure 2.0",
        "filename": "niva_bupa_reassure_2.txt",
        "pages": [
            """NIVA BUPA HEALTH INSURANCE COMPANY LIMITED
POLICY GUIDELINES: REASSURE 2.0 PLAN (Page 1)

SECTION 1: REVOLUTIONARY FEATURES
1.1 ReAssure Forever Benefit: Triggers 100% sum insured restoration after the first claim and stays active forever for all future claims in life.
1.2 Lock the Premium: Premium stays locked based on your entry age until you make your first claim! Age progression does not increase premium rate until a claim occurs.
1.3 Live Healthier Discount: Up to 30% discount on renewal premium based on step count tracked on Niva Bupa Health App.

SECTION 2: COVERAGE DETAILS
2.1 Room Category: Any room category up to Single Private Room covered without sub-limits.
2.2 Co-Payment: 0% co-payment. Option to opt for 10% or 20% voluntary co-payment for premium discount.
2.3 Pre-Hospitalization: 60 days.
2.4 Post-Hospitalization: 180 days.
2.5 Modern Treatments: CyberKnife, Intravitreal Injections, Deep Brain Stimulation, Bronchial Thermoplasty 100% covered.""",

            """NIVA BUPA HEALTH INSURANCE COMPANY LIMITED
POLICY GUIDELINES: REASSURE 2.0 PLAN (Page 2)

SECTION 3: WAITING PERIODS & EXCLUSIONS
3.1 Pre-Existing Disease (PED): 36 months waiting period for declared conditions. Option for 12/24 months reduction rider.
3.2 Specific Illnesses: 24 months for benign tumors, osteoarthritis, spinal surgery, hernia, cataract.
3.3 Exclusions: Hazardous sports, sleep apnea treatment, self-inflicted injuries, unproven alternative therapies.

SECTION 4: CLAIMS & HOSPITAL NETWORK
4.1 Hospital Network: 10,000+ cashless hospital partners across India.
4.2 Direct Claim Settlement: No TPA involvement; claims handled directly by in-house Niva Bupa claims team within 30 minutes.
4.3 Organ Donor Expense: Covered up to full sum insured."""
        ]
    }
]


def seed_policy_documents():
    """Create directory and generate text files for policy documents if directory is empty."""
    os.makedirs(SAMPLE_DOCS_DIR, exist_ok=True)
    if os.listdir(SAMPLE_DOCS_DIR):
        return []

    generated_files = []
    
    for doc_info in POLICY_DOCUMENTS:
        file_path = os.path.join(SAMPLE_DOCS_DIR, doc_info["filename"])
        full_content = "\n\n--- PAGE SEPARATOR ---\n\n".join(doc_info["pages"])
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content)
        
        generated_files.append(file_path)
    
    print(f"[SeedDocs] Successfully generated {len(generated_files)} policy text files in {SAMPLE_DOCS_DIR}")
    return generated_files



if __name__ == "__main__":
    seed_policy_documents()
