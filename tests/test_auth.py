import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

client = TestClient(app)


def test_auth_registration_and_login():
    """Test user registration, duplicate check, and login flow."""
    # Ensure fresh DB state
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # 1. Register User
    reg_payload = {
        "full_name": "Test User",
        "email": "testuser@clario.ai",
        "password": "Password123"
    }
    response = client.post("/api/v1/auth/register", json=reg_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testuser@clario.ai"

    # 2. Login User
    login_payload = {
        "email": "testuser@clario.ai",
        "password": "Password123"
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data

    # 3. Access Protected Profile
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    profile_res = client.get("/api/v1/profile", headers=headers)
    assert profile_res.status_code == 200
    assert profile_res.json()["age"] == 30


def test_missing_token_requires_authentication():
    """Test that missing bearer token is rejected on protected routes (unless demo mode is enabled)."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Attempt to access protected profile without token (should fail)
    response = client.get("/api/v1/profile")
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "Authentication required" in data["detail"] or "token" in data["detail"].lower()


def test_invalid_token_rejected():
    """Test that an invalid token is rejected."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Attempt with an invalid token format
    headers = {"Authorization": "Bearer invalid-token-xyz"}
    response = client.get("/api/v1/profile", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert "Invalid or expired" in data.get("detail", "") or "401" in str(response.status_code)


def test_malformed_token_rejected():
    """Test that a malformed token is rejected."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Test various malformed token formats
    malformed_tokens = [
        "invalid",
        "Bearer",
        "Bearer ",
        "Bearer ...",
        "x.y.z.extra"  # Too many parts for JWT
    ]
    
    for token in malformed_tokens:
        headers = {"Authorization": f"{token}".strip()}
        response = client.get("/api/v1/profile", headers=headers)
        # Should be rejected (either 401 or other auth error)
        assert response.status_code in [401, 403, 422], f"Token '{token}' should be rejected"
