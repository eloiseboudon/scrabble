"""Robustness tests for error conditions in game endpoints."""

import os
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

# Use SQLite database for tests
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi import HTTPException
from backend.database import Base, SessionLocal, engine  # type: ignore
from backend.main import (  # type: ignore
    AuthRequest,
    CreateGameRequest,
    JoinGameRequest,
    create_game,
    join_game,
    login,
    register,
    start_game,
)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def test_join_nonexistent_game() -> None:
    with SessionLocal() as db:
        try:
            join_game(9999, JoinGameRequest(user_id=1), db=db)
        except HTTPException as exc:
            assert exc.status_code == 404
        else:  # pragma: no cover - should not reach
            assert False


def test_start_game_insufficient_players() -> None:
    with SessionLocal() as db:
        game_id = create_game(CreateGameRequest(max_players=2), db=db)["game_id"]
    with SessionLocal() as db:
        join_game(game_id, JoinGameRequest(user_id=1), db=db)
    with SessionLocal() as db:
        try:
            start_game(game_id, db=db)
        except HTTPException as exc:
            assert exc.status_code == 400
            assert exc.detail == "insufficient_players"
        else:  # pragma: no cover
            assert False


def test_login_invalid_credentials() -> None:
    with SessionLocal() as db:
        register(AuthRequest(username="bob", password="pwd"), db=db)
    with SessionLocal() as db:
        try:
            login(AuthRequest(username="bob", password="wrong"), db=db)
        except HTTPException as exc:
            assert exc.status_code == 401
        else:  # pragma: no cover
            assert False
