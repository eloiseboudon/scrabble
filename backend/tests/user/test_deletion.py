import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from backend.main import app
from backend.database import SessionLocal
from backend import models
from backend.deletion import process_due_deletions

client = TestClient(app, base_url="http://localhost")


def test_user_deletion_flow() -> None:
    email = f"user-{uuid.uuid4()}@example.com"
    password = "secret1234"

    r = client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201
    user_id = r.json()["user_id"]

    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200

    # create game + gameplayer linked to user
    with SessionLocal() as db:
        game = models.Game(max_players=2)
        db.add(game)
        db.commit()
        db.refresh(game)
        gp = models.GamePlayer(game_id=game.id, user_id=user_id, rack="AAAAAAA")
        db.add(gp)
        db.commit()
        gp_id = gp.id

    r = client.post("/me/deletion-request")
    assert r.status_code == 200

    # force grace period to past and process
    with SessionLocal() as db:
        dr = db.query(models.DeletionRequest).filter_by(user_id=user_id).first()
        dr.grace_until = datetime.now(timezone.utc) - timedelta(days=1)
        db.commit()
        process_due_deletions(db)
        user = db.get(models.User, user_id)
        gp = db.get(models.GamePlayer, gp_id)
        dr = db.get(models.DeletionRequest, dr.id)
        assert user.deleted_at is not None
        assert user.display_name is None
        assert gp.user_id is None
        assert gp.display_name.startswith("Joueur anonyme")
        assert dr.status == "done"
