from app.rag.seed_docs import discover_policy_documents


def test_discover_embedded_policies_from_six_standalone_pdf():
    docs = discover_policy_documents()
    embedded = [
        d for d in docs
        if d.get("filename", "").startswith("Six_Standalone_Health_Insurance_Policies.pdf#policy_")
    ]

    assert len(embedded) == 6
    names = {d["policy_name"] for d in embedded}
    assert "SecureHealth Plus Individual" in names
    assert "Wellness Shield Pro Individual" in names
    assert "Guardian Health Advantage Individual" in names
