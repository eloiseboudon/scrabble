import os
import pathlib
import random
import sys
from unittest.mock import patch

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from backend.database import Base, SessionLocal, engine  # type: ignore
from backend.main import (
    CreateGameRequest,
    JoinGameRequest,
    MoveRequest,
    create_game,
    join_game,
    play_move,
    start_game,
    get_game_state,
)  # type: ignore

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def _setup_bot_game():
    random.seed(0)
    with SessionLocal() as db:
        game_id = create_game(CreateGameRequest(max_players=2, vs_computer=True), db=db)[
            "game_id"
        ]
    with SessionLocal() as db:
        p1 = join_game(game_id, JoinGameRequest(user_id=1), db=db)["player_id"]
    with SessionLocal() as db:
        p2 = join_game(game_id, JoinGameRequest(is_computer=True), db=db)["player_id"]
    with SessionLocal() as db:
        start_data = start_game(game_id, seed=0, db=db)
    rack1 = next(p["rack"] for p in start_data["players"] if p["player_id"] == p1)
    return game_id, p1, p2, rack1


def test_bot_move_triggered_after_player_turn():
    game_id, p1, _bot_id, rack1 = _setup_bot_game()
    placements = [
        {"row": 7, "col": 7, "letter": rack1[1], "blank": False},
        {"row": 7, "col": 8, "letter": rack1[3], "blank": False},
        {"row": 7, "col": 9, "letter": rack1[2], "blank": False},
    ]
    with patch(
        "backend.main.game_module.bot_turn", return_value=([(7, 10, "A", False)], 1)
    ), patch("backend.main.place_tiles", return_value=1):
        with SessionLocal() as db:
            res = play_move(game_id, MoveRequest(player_id=p1, placements=placements), db=db)
    assert "bot_move" in res
    assert res["next_player_id"] == p1
    with SessionLocal() as db:
        state = get_game_state(game_id, player_id=p1, db=db)
    assert len(state.tiles) == len(placements) + len(res["bot_move"])


def test_invalid_bot_move_keeps_turn():
    game_id, p1, bot_id, rack1 = _setup_bot_game()
    placements = [
        {"row": 7, "col": 7, "letter": rack1[1], "blank": False},
        {"row": 7, "col": 8, "letter": rack1[3], "blank": False},
        {"row": 7, "col": 9, "letter": rack1[2], "blank": False},
    ]
    with patch(
        "backend.main.game_module.bot_turn", return_value=([(0, 0, "A", False)], 1)
    ):
        with SessionLocal() as db:
            res = play_move(game_id, MoveRequest(player_id=p1, placements=placements), db=db)
    assert "bot_move" not in res
    assert res["next_player_id"] == bot_id


def test_state_fetch_triggers_pending_bot_move():
    game_id, p1, bot_id, rack1 = _setup_bot_game()
    placements = [
        {"row": 7, "col": 7, "letter": rack1[1], "blank": False},
        {"row": 7, "col": 8, "letter": rack1[3], "blank": False},
        {"row": 7, "col": 9, "letter": rack1[2], "blank": False},
    ]
    with patch("backend.main.game_module.bot_turn", return_value=None):
        with SessionLocal() as db:
            res = play_move(game_id, MoveRequest(player_id=p1, placements=placements), db=db)
    assert res["next_player_id"] == bot_id
    with patch(
        "backend.main.game_module.bot_turn", return_value=([(7, 10, "A", False)], 1)
    ), patch("backend.main.place_tiles", return_value=1):
        with SessionLocal() as db:
            state = get_game_state(game_id, player_id=p1, db=db)
    assert state.next_player_id == p1
    assert any(t.row == 7 and t.col == 10 for t in state.tiles)
