"""Integration tests for implemented game endpoints."""

import os
import pathlib
import random
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

# Use SQLite database for tests
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from backend.database import Base, SessionLocal, engine  # type: ignore
from fastapi import HTTPException
from backend.main import (
    AuthRequest,
    ChallengeRequest,
    CreateGameRequest,
    ExchangeRequest,
    JoinGameRequest,
    MoveRequest,
    PassRequest,
    ResignRequest,
    get_user_by_username,
    challenge_move,
    create_game,
    exchange_tiles,
    get_game_state,
    join_game,
    pass_turn,
    play_move,
    register,
    resign_game,
    start_game,
)  # type: ignore

Base.metadata.create_all(bind=engine)


def _setup_game() -> tuple[int, int, int, list[str]]:
    random.seed(0)
    with SessionLocal() as db:
        game_id = create_game(CreateGameRequest(max_players=2), db=db)["game_id"]
    with SessionLocal() as db:
        p1 = join_game(game_id, JoinGameRequest(user_id=1), db=db)["player_id"]
    with SessionLocal() as db:
        p2 = join_game(game_id, JoinGameRequest(user_id=2), db=db)["player_id"]
    with SessionLocal() as db:
        start_data = start_game(game_id, db=db)
    rack1 = next(p["rack"] for p in start_data["players"] if p["player_id"] == p1)
    return game_id, p1, p2, rack1


def test_game_lifecycle() -> None:
    game_id, p1, _p2, rack1 = _setup_game()
    assert len(rack1) == 7

    placements = [
        {"row": 7, "col": 7, "letter": "H", "blank": False},
        {"row": 7, "col": 8, "letter": "O", "blank": False},
        {"row": 7, "col": 9, "letter": "U", "blank": False},
    ]
    with SessionLocal() as db:
        score = play_move(game_id, MoveRequest(player_id=p1, placements=placements), db=db)[
            "score"
        ]
    assert score == 12

    with SessionLocal() as db:
        state = get_game_state(game_id, player_id=p1, db=db)
    assert len(state.rack) == 4
    assert state.bag_count == 102 - 14
    assert len(state.tiles) == 3


def test_exchange_pass_resign() -> None:
    game_id, p1, p2, rack1 = _setup_game()
    letter = rack1[0]
    with SessionLocal() as db:
        exchange = exchange_tiles(
            game_id, ExchangeRequest(player_id=p1, letters=[letter]), db=db
        )
    assert len(exchange["letters"]) == 1

    passed = pass_turn(game_id, PassRequest(player_id=p1))
    assert passed["status"] == "passed"

    challenged = challenge_move(game_id, ChallengeRequest(player_id=p2))
    assert "status" in challenged

    with SessionLocal() as db:
        resigned = resign_game(game_id, ResignRequest(player_id=p2), db=db)
    assert resigned["status"] == "resigned"


def test_user_lookup() -> None:
    with SessionLocal() as db:
        user_id = register(AuthRequest(username="alice", password="pwd"), db=db)[
            "user_id"
        ]
    with SessionLocal() as db:
        res = get_user_by_username("alice", db=db)
    assert res.user_id == user_id

    with SessionLocal() as db:
        try:
            get_user_by_username("unknown", db=db)
        except HTTPException as exc:
            assert exc.status_code == 404
        else:  # pragma: no cover - should not reach
            assert False
