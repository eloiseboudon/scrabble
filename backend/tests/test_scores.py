"""Additional tests for score reporting."""
import os
import pathlib
import random
import sys

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
