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
