"""FastAPI backend for Scrabble application."""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import models
from .database import get_db
from .game import DICTIONARY, draw_tiles, place_tiles, reset_game

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/validate")
def validate(word: str) -> dict[str, bool]:
    """Validate a word against the ODS8 dictionary."""
    return {"valid": word.upper() in DICTIONARY}


class Placement(BaseModel):
    row: int
    col: int
    letter: str
    blank: bool = False


class StartRequest(BaseModel):
    user_id: int | None = None
    max_players: int = 2
    vs_computer: bool = False


class PlayRequest(BaseModel):
    game_id: int
    user_id: int
    placements: list[Placement]


@app.post("/start")
def start(req: StartRequest, db: Session = Depends(get_db)) -> dict[str, int | list[str]]:
    """Start a new game and return identifiers and an initial rack."""
    reset_game()
    game = models.Game(max_players=req.max_players, vs_computer=req.vs_computer)
    db.add(game)
    db.flush()
    rack = draw_tiles(7)
    player = models.GamePlayer(game_id=game.id, user_id=req.user_id, rack="".join(rack))
    db.add(player)
    db.commit()
    return {"game_id": game.id, "player_id": player.id, "rack": rack}


@app.get("/draw")
def draw(n: int, player_id: int, db: Session = Depends(get_db)) -> dict[str, list[str]]:
    """Draw *n* new tiles from the bag and update the player's rack."""
    letters = draw_tiles(n)
    player = db.get(models.GamePlayer, player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    player.rack += "".join(letters)
    db.commit()
    return {"letters": letters}


@app.post("/play")
def play(req: PlayRequest, db: Session = Depends(get_db)) -> dict[str, int]:
    """Place tiles on the board, persist them and return the score."""
    try:
        score = place_tiles(
            [(p.row, p.col, p.letter.upper(), p.blank) for p in req.placements]
        )
    except ValueError as exc:  # pragma: no cover - simple passthrough
        raise HTTPException(status_code=400, detail=str(exc))

    for p in req.placements:
        tile = models.PlacedTile(
            game_id=req.game_id,
            user_id=req.user_id,
            x=p.row,
            y=p.col,
            letter=p.letter.upper(),
        )
        db.add(tile)

    player = (
        db.query(models.GamePlayer)
        .filter_by(game_id=req.game_id, user_id=req.user_id)
        .first()
    )
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    rack_list = list(player.rack)
    for p in req.placements:
        letter = "?" if p.blank else p.letter.upper()
        if letter in rack_list:
            rack_list.remove(letter)
    player.rack = "".join(rack_list)
    db.commit()
    return {"score": score}
