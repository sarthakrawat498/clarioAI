from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


client = TestClient(app)


def test_upload_policy_document_extracts_key_fields_and_updates_recommendations():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    sample_text = """
    Policy Name: Demo Secure Plan
    Sum Assured: 10 Lakhs
    Annual Premium: Rs. 18,500
    Room Rent: No room rent capping
    Co-Pay: 10%
    PED Waiting Period: 24 months
    Restoration Benefit: 100% restore benefit
    No Claim Bonus: 50%
    Pre-Hospitalization: 60 days
    Post-Hospitalization: 180 days
    Daycare Treatments: Covered
    Air Ambulance: Covered
    Claim Settlement Ratio: 97%
    Network Hospitals: 12000

    Benefits:
    - No room rent capping
    - 100% restore benefit
    - Cashless hospitalization across network hospitals
    """.strip()

    upload_response = client.post(
        "/api/v1/documents/upload-policy",
        files={"file": ("demo_policy.txt", sample_text.encode("utf-8"), "text/plain")},
    )

    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert upload_data["message"] == "Policy document analyzed successfully."
    assert upload_data["session_id"] is not None
    assert upload_data["snapshot"]["policy_name"] == "Demo Secure Plan"
    assert upload_data["snapshot"]["sum_assured_amount"] == 1000000.0
    assert upload_data["snapshot"]["premium_amount"] == 18500.0
    assert len(upload_data["snapshot"]["benefits"]) >= 2
    assert upload_data["snapshot"]["extracted_summary"]["room_rent_limit"] == "No room rent capping"
    assert upload_data["snapshot"]["extracted_summary"]["co_pay_percentage"] == 10.0
    assert upload_data["snapshot"]["extracted_summary"]["ped_waiting_period_months"] == 24
    assert upload_data["snapshot"]["extracted_summary"]["restoration_benefit"] == "100% restore benefit"
    assert upload_data["snapshot"]["extracted_summary"]["no_claim_bonus"] == "50%"
    assert upload_data["snapshot"]["extracted_summary"]["pre_hospitalization_days"] == 60
    assert upload_data["snapshot"]["extracted_summary"]["post_hospitalization_days"] == 180
    assert upload_data["snapshot"]["extracted_summary"]["daycare_treatments_covered"] is True
    assert upload_data["snapshot"]["extracted_summary"]["air_ambulance_cover"] is True
    assert upload_data["snapshot"]["extracted_summary"]["claim_settlement_ratio"] == 97.0
    assert upload_data["snapshot"]["extracted_summary"]["network_hospitals_count"] == 12000

    recommendations_response = client.get("/api/v1/recommendations")
    assert recommendations_response.status_code == 200
    recommendations_data = recommendations_response.json()
    assert "uploaded policy" not in recommendations_data["general_advice"].lower()


def test_upload_policy_document_extracts_table_style_pdf_rows():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    sample_text = """
    SAMPLE / DEMONSTRATION DOCUMENT
    HEALTH INSURANCE POLICY DOCUMENT
    WellCare Shield Individual - Policy Schedule & Terms

    Field    Details
    Policyholder    Rohan Sharma
    Policy Number   HIN-IND-2026-593417
    Plan Name   WellCare Shield Individual
    Insurer    NovaCare Health Insurance Company Ltd. (Fictional)
    Policy Type   Individual Health Insurance
    Sum Insured   12,00,000
    Annual Premium   27,450 (including applicable taxes)
    Policy Period   14 August 2026 - 13 August 2027
    Policy Status  Active

    Coverage Summary
    Benefit    Limit / Coverage Notes
    Hospitalisation   Up to 12,00,000 -- For admissible expenses during covered hospitalization
    Pre-hospitalisation   60 days -- Subject to admissibility and policy conditions
    Post-hospitalisation  180 days -- Subject to admissibility and policy conditions
    Day-care Procedures   Covered -- As per insurer's approved day-care list / terms
    Ambulance   Up to 7,500 per event -- For covered hospitalisation
    Room Rent   Up to 1% of Sum Insured/day -- Subject to policy schedule
    ICU   Up to 2% of Sum Insured/day -- Subject to policy schedule
    Domiciliary Treatment   Up to 2,50,000 -- Subject to eligibility conditions
    Health Check-up   Up to 4,000/year -- Subject to policy terms
    Organ Donor Expenses   Covered -- For admissible donor-related hospital expenses
    """.strip()

    upload_response = client.post(
        "/api/v1/documents/upload-policy",
        files={"file": ("wellcare_shield.txt", sample_text.encode("utf-8"), "text/plain")},
    )

    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert upload_data["snapshot"]["policy_name"] == "WellCare Shield Individual"
    assert upload_data["snapshot"]["sum_assured_amount"] == 1200000.0
    assert upload_data["snapshot"]["premium_amount"] == 27450.0
    assert upload_data["snapshot"]["extracted_summary"]["room_rent_limit"] == "Up to 1% of Sum Insured/day"
    assert upload_data["snapshot"]["extracted_summary"]["pre_hospitalization_days"] == 60
    assert upload_data["snapshot"]["extracted_summary"]["post_hospitalization_days"] == 180
