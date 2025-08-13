"""Tests for game state validation and turn handling."""

import os
import pathlib
import random
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

# Use SQLite database for tests
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi import HTTPException  # type: ignore
from backend.database import Base, SessionLocal, engine  # type: ignore
from backend.api.games import (
    CreateGameRequest,
    JoinGameRequest,
    MoveRequest,
    create_game,
    get_game_state,
    join_game,
    play_move,
    start_game,
)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def _setup() -> tuple[int, int, int, dict]:
    random.seed(0)
    with SessionLocal() as db:
        gid = create_game(CreateGameRequest(max_players=2), db=db)["game_id"]
    with SessionLocal() as db:
        p1 = join_game(gid, JoinGameRequest(user_id=1), db=db)["player_id"]
    with SessionLocal() as db:
        p2 = join_game(gid, JoinGameRequest(user_id=2), db=db)["player_id"]
    with SessionLocal() as db:
        start = start_game(gid, seed=0, db=db)
    return gid, p1, p2, start


def test_join_after_start_forbidden() -> None:
    gid, p1, p2, _start = _setup()
    with SessionLocal() as db:
        try:
            join_game(gid, JoinGameRequest(user_id=3), db=db)
        except HTTPException as exc:
            assert exc.status_code == 409
            assert exc.detail == "game_already_started"
        else:  # pragma: no cover - should not reach
            assert False


def test_turn_enforcement_and_counts() -> None:
    gid, p1, p2, _start = _setup()
    placements = [
        {"row": 7, "col": 7, "letter": "H", "blank": False},
        {"row": 7, "col": 8, "letter": "O", "blank": False},
        {"row": 7, "col": 9, "letter": "U", "blank": False},
    ]
    with SessionLocal() as db:
        try:
            play_move(gid, MoveRequest(player_id=p2, placements=placements), db=db)
        except HTTPException as exc:
            assert exc.status_code == 409
            assert exc.detail == "not_your_turn"
        else:  # pragma: no cover
            assert False
    with SessionLocal() as db:
        res = play_move(gid, MoveRequest(player_id=p1, placements=placements), db=db)
    assert res["next_player_id"] == p2
    assert res["scores"][p1] == res["score"]
    assert res["bag_count"] == 102 - 14 - 3
    with SessionLocal() as db:
        state1 = get_game_state(gid, player_id=p1, db=db)
    with SessionLocal() as db:
        state2 = get_game_state(gid, player_id=p2, db=db)
    total = res["bag_count"] + len(state1.rack) + len(state2.rack) + len(state1.tiles)
    assert total == 102
