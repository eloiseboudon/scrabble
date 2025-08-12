from fastapi.testclient import TestClient
import uuid

from backend.main import app

client = TestClient(app)


def test_register_and_login() -> None:
    username = f"user-{uuid.uuid4()}"
    password = "secret"
    r = client.post("/register", json={"username": username, "password": password})
    assert r.status_code == 200
    user_id = r.json()["user_id"]

    r = client.post("/login", json={"username": username, "password": password})
    assert r.status_code == 200
    assert r.json()["user_id"] == user_id
