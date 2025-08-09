"""FastAPI backend for Scrabble application."""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import hashlib

from . import models
from .database import get_db
from .game import DICTIONARY, draw_tiles, load_game_state, place_tiles, reset_game

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


class FinishRequest(BaseModel):
    game_id: int


class GameInfo(BaseModel):
    id: int
    player_id: int


class GamesResponse(BaseModel):
    ongoing: list[GameInfo]
    finished: list[GameInfo]


class Tile(BaseModel):
    row: int
    col: int
    letter: str


class GameState(BaseModel):
    rack: list[str]
    tiles: list[Tile]


class AuthRequest(BaseModel):
    """Request model for user authentication."""
    username: str
    password: str


@app.post("/register")
def register(req: AuthRequest, db: Session = Depends(get_db)) -> dict[str, int]:
    """Create a new user and return its identifier."""
    if db.query(models.User).filter_by(username=req.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed = hashlib.sha256(req.password.encode()).hexdigest()
    user = models.User(username=req.username, hashed_password=hashed)
    db.add(user)
    db.commit()
    return {"user_id": user.id}


@app.post("/login")
def login(req: AuthRequest, db: Session = Depends(get_db)) -> dict[str, int]:
    """Authenticate a user and return its identifier."""
    hashed = hashlib.sha256(req.password.encode()).hexdigest()
    user = (
        db.query(models.User)
        .filter_by(username=req.username, hashed_password=hashed)
        .first()
    )
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"user_id": user.id}


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


@app.post("/finish")
def finish(req: FinishRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    """Mark a game as finished."""
    game = db.get(models.Game, req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    game.finished = True
    db.commit()
    return {"status": "ok"}


@app.get("/games")
def list_games(user_id: int, db: Session = Depends(get_db)) -> GamesResponse:
    """Return games for a user, separated by status."""
    records = (
        db.query(models.Game, models.GamePlayer)
        .join(models.GamePlayer)
        .filter(models.GamePlayer.user_id == user_id)
        .all()
    )
    ongoing: list[GameInfo] = []
    finished: list[GameInfo] = []
    for game, player in records:
        info = GameInfo(id=game.id, player_id=player.id)
        if game.finished:
            finished.append(info)
        else:
            ongoing.append(info)
    return GamesResponse(ongoing=ongoing, finished=finished)


@app.get("/game")
def get_game(game_id: int, player_id: int, db: Session = Depends(get_db)) -> GameState:
    """Retrieve a game's state, rebuilding board and returning rack and tiles."""
    tiles = db.query(models.PlacedTile).filter_by(game_id=game_id).all()
    players = db.query(models.GamePlayer).filter_by(game_id=game_id).all()
    load_game_state([(t.x, t.y, t.letter) for t in tiles], [p.rack for p in players])
    player = (
        db.query(models.GamePlayer)
        .filter_by(game_id=game_id, id=player_id)
        .first()
    )
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return GameState(
        rack=list(player.rack),
        tiles=[Tile(row=t.x, col=t.y, letter=t.letter) for t in tiles],
    )


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
