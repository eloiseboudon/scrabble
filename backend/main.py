"""FastAPI backend for Scrabble application."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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


class PlayRequest(BaseModel):
    placements: list[Placement]


@app.post("/start")
def start() -> dict[str, list[str]]:
    """Start a new game and return an initial rack of seven tiles."""
    reset_game()
    rack = draw_tiles(7)
    return {"rack": rack}


@app.get("/draw")
def draw(n: int) -> dict[str, list[str]]:
    """Draw *n* new tiles from the bag."""
    letters = draw_tiles(n)
    return {"letters": letters}


@app.post("/play")
def play(req: PlayRequest) -> dict[str, int]:
    """Place tiles on the board and return the score for the move."""
    try:
        score = place_tiles(
            [(p.row, p.col, p.letter.upper(), p.blank) for p in req.placements]
        )
    except ValueError as exc:  # pragma: no cover - simple passthrough
        raise HTTPException(status_code=400, detail=str(exc))
    return {"score": score}
