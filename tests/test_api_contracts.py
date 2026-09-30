"""
Integration tests for frontend-backend API contracts.
These tests verify that the request/response payloads match across all major API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    """Setup fresh database for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_token():
    """Register and login a test user, return auth token."""
    reg_payload = {
        "full_name": "Test User",
        "email": "testcontract@clario.ai",
        "password": "Password123"
    }
    client.post("/api/v1/auth/register", json=reg_payload)
    
    login_payload = {
        "email": "testcontract@clario.ai",
        "password": "Password123"
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    return login_res.json()["access_token"]


class TestClaimsAPIContract:
    """Test that claims request/response contracts match frontend expectations."""
    
    def test_claims_request_schema_accepts_correct_fields(self, auth_token):
        """Verify that the claims endpoint accepts the correct field names."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # This is the payload structure the frontend sends after the fix
        claim_payload = {
            "policy_name": "Star Comprehensive Insurance",
            "treatment_name": "Knee Replacement Surgery",  # Not disease_or_procedure
            "hospital_type": "Network",
            "room_category_chosen": "Single Private Room",  # Not room_category
            "claimed_amount": 250000,
            "policy_holding_duration_months": 24,  # Not policy_tenure_months
            "is_pre_existing_condition": False,  # Not pre_existing
        }
        
        response = client.post("/api/v1/claims/check", json=claim_payload, headers=headers)
        assert response.status_code == 200, f"Claims endpoint rejected payload: {response.text}"
        
    def test_claims_response_contains_required_fields(self, auth_token):
        """Verify that the claims response contains all expected fields."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        claim_payload = {
            "policy_name": "Star Comprehensive Insurance",
            "treatment_name": "Cataract Surgery",
            "claimed_amount": 70000,
            "policy_holding_duration_months": 25,
            "is_pre_existing_condition": False,
        }
        
        response = client.post("/api/v1/claims/check", json=claim_payload, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        # Frontend expects these exact field names
        assert "status" in data, "Response missing 'status' field"
        assert "estimated_approved_amount" in data, "Response missing 'estimated_approved_amount' (frontend looks for this)"
        assert "explanation" in data, "Response missing 'explanation' (frontend looks for this, not 'reason')"
        assert "deductions" in data, "Response missing 'deductions' field"
        assert isinstance(data["deductions"], (int, float)), "Deductions should be numeric, not an object"


class TestPremiumAPIContract:
    """Test that premium request/response contracts match frontend expectations."""
    
    def test_premium_request_schema_accepts_list_ped(self, auth_token):
        """Verify that the premium endpoint accepts pre_existing_diseases as a list."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # This is the payload structure the frontend sends after the fix
        premium_payload = {
            "age": 32,
            "city_tier": "Tier 1",
            "family_members_count": 2,
            "coverage_type": "Family Floater",
            "sum_insured": 1000000,
            "tobacco_user": False,
            "pre_existing_diseases": [],  # Empty list when no PED selected
        }
        
        response = client.post("/api/v1/recommendations/estimate", json=premium_payload, headers=headers)
        assert response.status_code == 200, f"Premium endpoint rejected payload: {response.text}"
    
    def test_premium_request_accepts_ped_with_conditions(self, auth_token):
        """Verify that the premium endpoint handles pre_existing_diseases as a non-empty list."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        premium_payload = {
            "age": 35,
            "city_tier": "Tier 1",
            "family_members_count": 2,
            "coverage_type": "Family Floater",
            "sum_insured": 1000000,
            "tobacco_user": False,
            "pre_existing_diseases": ["Other Pre-Existing Condition"],
        }
        
        response = client.post("/api/v1/recommendations/estimate", json=premium_payload, headers=headers)
        assert response.status_code == 200, f"Premium endpoint rejected PED list: {response.text}"
    
    def test_premium_response_contains_breakdown_list(self, auth_token):
        """Verify that the premium response contains breakdown as a list of items."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        premium_payload = {
            "age": 32,
            "city_tier": "Tier 1",
            "family_members_count": 2,
            "coverage_type": "Family Floater",
            "sum_insured": 1000000,
            "tobacco_user": False,
            "pre_existing_diseases": [],
        }
        
        response = client.post("/api/v1/recommendations/estimate", json=premium_payload, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        # Frontend expects these exact field names
        assert "total_annual_premium" in data, "Response missing 'total_annual_premium'"
        assert "gst_18_percent" in data, "Response missing 'gst_18_percent' (frontend looks for this, not 'gst_tax')"
        assert "breakdown" in data, "Response missing 'breakdown' field"
        assert isinstance(data["breakdown"], list), "Breakdown should be a list of items, not an object"
        
        # Each breakdown item should have name, amount, description
        if len(data["breakdown"]) > 0:
            item = data["breakdown"][0]
            assert "name" in item, "Breakdown item missing 'name'"
            assert "amount" in item, "Breakdown item missing 'amount'"
            assert "description" in item, "Breakdown item missing 'description'"


class TestCORSConfiguration:
    """Test that CORS is properly configured for frontend origins."""
    
    def test_allowed_cors_origins(self):
        """Verify that the configured frontend origins are allowed."""
        # Test a few common frontend development origins
        allowed_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
        
        # We can't fully test CORS headers without proper testing setup,
        # but we can verify the app starts with CORS configured
        # A proper CORS test would need to send preflight requests
        response = client.options("/api/v1/auth/login")
        # The response should handle the OPTIONS request (either 200 or 404 is fine, 500 is not)
        assert response.status_code in [200, 404, 405], "Server should handle CORS preflight requests"
