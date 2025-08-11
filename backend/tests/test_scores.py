"""Additional tests for score reporting."""
import os
import pathlib
import random
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi import HTTPException  # type: ignore

from backend import models  # type: ignore
from backend.database import Base, SessionLocal, engine  # type: ignore
from backend.main import (
    CreateGameRequest,
    JoinGameRequest,
    MoveRequest,
    create_game,
    join_game,
    play_move,
    get_game_state,
    start_game,
)  # type: ignore

Base.metadata.drop_all(bind=engine)
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
        start_data = start_game(game_id, seed=0, db=db)
    rack1 = next(p["rack"] for p in start_data["players"] if p["player_id"] == p1)
    return game_id, p1, p2, rack1


def test_scores_report_both_players() -> None:
    game_id, p1, p2, rack1 = _setup_game()
    placements = [
        {"row": 7, "col": 7, "letter": rack1[1], "blank": False},
        {"row": 7, "col": 8, "letter": rack1[3], "blank": False},
        {"row": 7, "col": 9, "letter": rack1[2], "blank": False},
    ]
    with SessionLocal() as db:
        play_move(game_id, MoveRequest(player_id=p1, placements=placements), db=db)
    with SessionLocal() as db:
        state = get_game_state(game_id, player_id=p2, db=db)
    assert state.scores[p1] > 0
    assert state.scores[p2] == 0


def test_scrabble_bonus_and_refill() -> None:
    game_id, p1, p2, _rack1 = _setup_game()
    with SessionLocal() as db:
        player = db.get(models.GamePlayer, p1)
        assert player is not None
        player.rack = "BANANES"
        db.commit()
    placements = [
        {"row": 7, "col": 7, "letter": "B", "blank": False},
        {"row": 7, "col": 8, "letter": "A", "blank": False},
        {"row": 7, "col": 9, "letter": "N", "blank": False},
        {"row": 7, "col": 10, "letter": "A", "blank": False},
        {"row": 7, "col": 11, "letter": "N", "blank": False},
        {"row": 7, "col": 12, "letter": "E", "blank": False},
        {"row": 7, "col": 13, "letter": "S", "blank": False},
    ]
    with SessionLocal() as db:
        res = play_move(game_id, MoveRequest(player_id=p1, placements=placements), db=db)
    assert res["score"] == 70
    assert res["scores"][p1] == 70
    with SessionLocal() as db:
        state1 = get_game_state(game_id, player_id=p1, db=db)
    with SessionLocal() as db:
        state2 = get_game_state(game_id, player_id=p2, db=db)
    assert len(state1.rack) == 7
    total = res["bag_count"] + len(state1.rack) + len(state2.rack) + len(state1.tiles)
    assert total == 102


def test_blank_tile_scoring_and_persistence() -> None:
    game_id, p1, _p2, _rack1 = _setup_game()
    with SessionLocal() as db:
        player = db.get(models.GamePlayer, p1)
        assert player is not None
        player.rack = "PI?ZAAB"
        db.commit()
    placements = [
        {"row": 7, "col": 7, "letter": "P", "blank": False},
        {"row": 7, "col": 8, "letter": "I", "blank": False},
        {"row": 7, "col": 9, "letter": "Z", "blank": False},
        {"row": 7, "col": 10, "letter": "Z", "blank": True},
        {"row": 7, "col": 11, "letter": "A", "blank": False},
    ]
    with SessionLocal() as db:
        res = play_move(game_id, MoveRequest(player_id=p1, placements=placements), db=db)
    assert res["score"] == 32
    with SessionLocal() as db:
        state = get_game_state(game_id, player_id=p1, db=db)
    tile_map = {(t.row, t.col): t.letter for t in state.tiles}
    assert tile_map[(7, 10)] == "z"


def test_first_move_requires_center() -> None:
    game_id, p1, _p2, rack1 = _setup_game()
    placements = [
        {"row": 0, "col": 0, "letter": rack1[0], "blank": False},
        {"row": 0, "col": 1, "letter": rack1[1], "blank": False},
    ]
    with SessionLocal() as db:
        try:
            play_move(game_id, MoveRequest(player_id=p1, placements=placements), db=db)
        except HTTPException as exc:
            assert exc.status_code == 400
            assert exc.detail == "First move must cover the center square"
        else:  # pragma: no cover
            assert False


def test_multipliers_not_reused_on_extension() -> None:
    game_id, p1, p2, _rack1 = _setup_game()
    with SessionLocal() as db:
        pl1 = db.get(models.GamePlayer, p1)
        pl2 = db.get(models.GamePlayer, p2)
        assert pl1 is not None and pl2 is not None
        pl1.rack = "FAAAAAA"
        pl2.rack = "RBBBBBB"
        db.commit()
    placements1 = [
        {"row": 7, "col": 7, "letter": "F", "blank": False},
        {"row": 7, "col": 8, "letter": "A", "blank": False},
    ]
    with SessionLocal() as db:
        res1 = play_move(game_id, MoveRequest(player_id=p1, placements=placements1), db=db)
    assert res1["score"] == 10
    placements2 = [{"row": 7, "col": 9, "letter": "R", "blank": False}]
    with SessionLocal() as db:
        res2 = play_move(game_id, MoveRequest(player_id=p2, placements=placements2), db=db)
    assert res2["score"] == 6
