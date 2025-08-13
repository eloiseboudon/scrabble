import uuid

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app, base_url="http://localhost")


def test_auth_flow() -> None:
    email = f"user-{uuid.uuid4()}@example.com"
    password = "secret1234"  # ≥ 8 caractères, conforme à la nouvelle policy

    # Register -> 201 + user_id
    r = client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201
    user_id = r.json()["user_id"]

    # Login -> 200 + cookies access/refresh
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    assert r.json()["user_id"] == user_id
    assert client.cookies.get("access_token") is not None
    assert client.cookies.get("refresh_token") is not None

    # Sauvegarde du refresh avant rotation
    refresh_before = client.cookies.get("refresh_token")

    # Refresh -> 200 + rotation (nouveau refresh) + nouveau access
    r = client.post("/auth/refresh")
    assert r.status_code == 200
    assert client.cookies.get("access_token") is not None
    assert client.cookies.get("refresh_token") is not None
    assert client.cookies.get("refresh_token") != refresh_before  # rotation OK

    # /auth/me -> 200 + email
    r = client.get("/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == email
    assert r.json()["color_palette"] == "palette1"
    assert r.json()["avatar_url"] == "/img/icone/avatars/default1.svg"

    # Update palette
    r = client.post("/auth/me/palette", json={"palette": "palette2"})
    assert r.status_code == 200
    assert r.json()["color_palette"] == "palette2"
    r = client.get("/auth/me")
    assert r.status_code == 200
    assert r.json()["color_palette"] == "palette2"

    # Logout -> 200 + cookies supprimés
    r = client.post("/auth/logout")
    assert r.status_code == 200
    assert client.cookies.get("access_token") is None
    assert client.cookies.get("refresh_token") is None

    # Public user info endpoint returns avatar
    r = client.get(f"/users/{user_id}")
    assert r.status_code == 200
    assert r.json()["avatar_url"] == "/img/icone/avatars/default1.svg"
