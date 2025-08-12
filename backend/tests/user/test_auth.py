from fastapi.testclient import TestClient
import uuid

from backend.main import app


client = TestClient(app, base_url="http://localhost")


def test_auth_flow() -> None:
    email = f"user-{uuid.uuid4()}@example.com"
    password = "secret"

    r = client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200
    user_id = r.json()["user_id"]

    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    assert r.json()["user_id"] == user_id
    assert "access_token" in r.cookies
    assert "refresh_token" in r.cookies

    r = client.post("/auth/refresh", cookies={"refresh_token": client.cookies.get("refresh_token")})
    assert r.status_code == 200
    assert "access_token" in r.cookies

    r = client.get("/auth/me", cookies={"access_token": client.cookies.get("access_token")})
    assert r.status_code == 200
    assert r.json()["email"] == email

    r = client.post("/auth/logout")
    assert r.status_code == 200
