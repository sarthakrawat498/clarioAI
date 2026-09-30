import pytest
from app.rag.vector_store import vector_store_manager


def test_vector_store_ingestion_and_query():
    """Test document ingestion into ChromaDB and metadata-aware retrieval."""
    vector_store_manager.ingest_all_sample_policies()
    
    # Query HDFC Optima Secure specific clause
    results = vector_store_manager.query(
        query_text="room rent limit secure benefit double sum insured",
        n_results=2,
        company_filter="HDFC ERGO"
    )
    
    assert len(results) > 0
    assert results[0]["company"] == "HDFC ERGO"
    assert "page" in results[0]
    assert "citation" in results[0]


def test_vector_store_query_with_company_and_policy_filter():
    """Metadata filtering should work when both company and policy filters are applied together."""
    vector_store_manager.ingest_all_sample_policies()

    results = vector_store_manager.query(
        query_text="room rent restore benefit",
        n_results=2,
        company_filter="HDFC ERGO",
        policy_filter="Optima Secure",
    )

    assert len(results) > 0
    assert all(item["company"] == "HDFC ERGO" for item in results)
    assert all(item["policy_name"] == "Optima Secure" for item in results)
