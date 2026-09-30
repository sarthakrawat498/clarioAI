from app.main import app
from app.database import Base, engine, SessionLocal
from app.models.profile import ProfileSnapshot
from fastapi.testclient import TestClient


client = TestClient(app)


def test_profile_updates_create_snapshots_and_recommendations_can_target_them():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    reg_payload = {
        "full_name": "Snapshot User",
        "email": "snapshot@clario.ai",
        "password": "Password123",
    }
    register_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert register_res.status_code == 201

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "snapshot@clario.ai", "password": "Password123"},
    )
    assert login_res.status_code == 200
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    profile_res = client.get("/api/v1/profile", headers=headers)
    assert profile_res.status_code == 200
    first_snapshot_id = profile_res.json()["active_profile_session_id"]
    assert first_snapshot_id is not None

    with SessionLocal() as db:
        assert db.query(ProfileSnapshot).filter(ProfileSnapshot.user_id == profile_res.json()["user_id"]).count() == 1

    update_res = client.put(
        "/api/v1/profile",
        headers=headers,
        json={
            "age": 45,
            "gender": "Female",
            "city": "Mumbai",
            "coverage_type": "Individual",
            "pre_existing_diseases": ["Diabetes Mellitus"],
            "sum_insured_preference": 1500000,
            "budget_annual_max": 25000,
        },
    )
    assert update_res.status_code == 200
    second_snapshot_id = update_res.json()["active_profile_session_id"]
    assert second_snapshot_id is not None
    assert second_snapshot_id != first_snapshot_id

    with SessionLocal() as db:
        assert db.query(ProfileSnapshot).filter(ProfileSnapshot.user_id == profile_res.json()["user_id"]).count() == 2

    latest_recommendations = client.get("/api/v1/recommendations", headers=headers)
    assert latest_recommendations.status_code == 200
    assert latest_recommendations.json()["user_profile_summary"]["age"] == 45

    historical_recommendations = client.get(
        f"/api/v1/recommendations?profile_session_id={first_snapshot_id}",
        headers=headers,
    )
    assert historical_recommendations.status_code == 200
    assert historical_recommendations.json()["user_profile_summary"]["age"] == 30