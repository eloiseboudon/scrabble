"""FastAPI backend for Scrabble application."""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import hashlib
import logging
import random

from . import game as game_module, models
from .database import get_db
from .game import DICTIONARY, draw_tiles, load_game_state, place_tiles, reset_game

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,  # ou DEBUG
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
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


class CreateGameRequest(BaseModel):
    max_players: int = 2
    vs_computer: bool = False


class JoinGameRequest(BaseModel):
    user_id: int | None = None
    is_computer: bool = False


class MoveRequest(BaseModel):
    player_id: int
    placements: list[Placement]


class ExchangeRequest(BaseModel):
    player_id: int
    letters: list[str]


class PassRequest(BaseModel):
    player_id: int


class ChallengeRequest(BaseModel):
    player_id: int


class ResignRequest(BaseModel):
    player_id: int


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
    bag_count: int
    next_player_id: int
    scores: dict[int, int]
    passes_in_a_row: int
    phase: str


def _state_response(game: models.Game, players: list[models.GamePlayer]) -> dict[str, object]:
    """Build a state dictionary with common game fields."""
    return {
        "next_player_id": game.next_player_id if game.next_player_id is not None else 0,
        "bag_count": len(game_module.bag),
        "scores": {p.id: p.score for p in players},
        "passes_in_a_row": game.passes_in_a_row,
        "phase": game.phase,
    }


def _maybe_play_bot(
    game_id: int, game: models.Game, db: Session
) -> tuple[list[models.GamePlayer], list[tuple[int, int, str, bool]] | None, int]:
    """Attempt to play a bot move if it's the bot's turn.

    Returns updated players list, the bot move if any, and the bot score.
    """
    logger.info(
        "Checking bot move for game %s: next=%s vs_computer=%s",
        game_id,
        game.next_player_id,
        game.vs_computer,
    )
    players = db.query(models.GamePlayer).filter_by(game_id=game_id).all()
    bot_move: list[tuple[int, int, str, bool]] | None = None
    bot_score = 0
    if not game.vs_computer:
        logger.debug("Game %s is not against a computer", game_id)
        return players, bot_move, bot_score

    bot_player = next((p for p in players if p.is_computer), None)
    if not bot_player:
        logger.warning("Game %s marked vs_computer but no bot player found", game_id)
        return players, bot_move, bot_score

    if game.next_player_id != bot_player.id:
        logger.debug(
            "Game %s bot player id %s but next player is %s",
            game_id,
            bot_player.id,
            game.next_player_id,
        )
        return players, bot_move, bot_score

    logger.info("Game %s bot %s attempting move", game_id, bot_player.id)
    move = game_module.bot_turn(list(bot_player.rack))
    logger.debug("Game %s bot_turn result: %s", game_id, move)
    if not move:
        logger.info("Game %s bot could not find a move", game_id)
        return players, bot_move, bot_score

    move_tiles, _ = move
    if move_tiles:
        try:
            bot_score = place_tiles(move_tiles)
            logger.info(
                "Game %s bot placed tiles %s scoring %s",
                game_id,
                move_tiles,
                bot_score,
            )
        except ValueError as exc:
            logger.warning(
                "Game %s bot produced invalid move %s: %s",
                game_id,
                move_tiles,
                exc,
            )
            move_tiles = []
    if not move_tiles:
        logger.info("Game %s bot has no valid move", game_id)
        return players, bot_move, bot_score

    bot_move = move_tiles
    rack_bot = list(bot_player.rack)
    for r, c, letter, blank in bot_move:
        tile = models.PlacedTile(
            game_id=game_id,
            player_id=bot_player.id,
            x=r,
            y=c,
            letter=letter.upper(),
        )
        db.add(tile)
        ltr = "?" if blank else letter.upper()
        if ltr in rack_bot:
            rack_bot.remove(ltr)
    drawn_bot = draw_tiles(7 - len(rack_bot))
    rack_bot.extend(drawn_bot)
    bot_player.rack = "".join(rack_bot)
    bot_player.score += bot_score
    players_sorted = sorted(players, key=lambda pl: pl.id)
    idx_bot = next(i for i, pl in enumerate(players_sorted) if pl.id == bot_player.id)
    game.next_player_id = players_sorted[(idx_bot + 1) % len(players_sorted)].id
    game.passes_in_a_row = 0
    db.commit()
    logger.info(
        "Game %s bot move committed, next player %s", game_id, game.next_player_id
    )
    players = db.query(models.GamePlayer).filter_by(game_id=game_id).all()
    return players, bot_move, bot_score


class AuthRequest(BaseModel):
    """Request model for user authentication."""
    username: str
    password: str


class UserLookupResponse(BaseModel):
    """Response model for user lookup by username."""
    user_id: int


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


@app.get("/users/by-username")
def get_user_by_username(
    username: str, db: Session = Depends(get_db)
) -> UserLookupResponse:
    """Retrieve a user's identifier by their username."""
    user = db.query(models.User).filter_by(username=username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    return UserLookupResponse(user_id=user.id)


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
    game = db.get(models.Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    load_game_state([(t.x, t.y, t.letter) for t in tiles], [p.rack for p in players])
    player = (
        db.query(models.GamePlayer)
        .filter_by(game_id=game_id, id=player_id)
        .first()
    )
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    state = _state_response(game, players)
    return GameState(
        rack=list(player.rack),
        tiles=[Tile(row=t.x, col=t.y, letter=t.letter) for t in tiles],
        **state,
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


@app.post("/games")
def create_game(req: CreateGameRequest, db: Session = Depends(get_db)) -> dict[str, int]:
    """Create a new game and return its identifier."""
    game = models.Game(max_players=req.max_players, vs_computer=req.vs_computer)
    db.add(game)
    db.commit()
    return {"game_id": game.id}


@app.post("/games/{game_id}/join")
def join_game(game_id: int, req: JoinGameRequest, db: Session = Depends(get_db)) -> dict[str, int]:
    """Join an existing game and return the created player identifier."""
    game = db.get(models.Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.started:
        raise HTTPException(status_code=409, detail="game_already_started")
    count = db.query(models.GamePlayer).filter_by(game_id=game_id).count()
    if count >= game.max_players:
        raise HTTPException(status_code=409, detail="game_full")
    player = models.GamePlayer(
        game_id=game_id,
        user_id=req.user_id,
        is_computer=req.is_computer,
        rack="",
    )
    db.add(player)
    db.commit()
    return {"player_id": player.id}


@app.post("/games/{game_id}/start")
def start_game(
    game_id: int, seed: int | None = None, db: Session = Depends(get_db)
) -> dict[str, object]:
    """Start a game once enough players have joined."""
    game = db.get(models.Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    players = db.query(models.GamePlayer).filter_by(game_id=game_id).all()
    if len(players) < 2:
        raise HTTPException(status_code=400, detail="insufficient_players")
    if seed is not None:
        random.seed(seed)
    reset_game()
    info: list[dict[str, object]] = []
    for p in players:
        rack = draw_tiles(7)
        p.rack = "".join(rack)
        p.score = 0
        info.append({"player_id": p.id, "rack": rack})
    game.started = True
    game.phase = "running"
    game.next_player_id = players[0].id
    game.passes_in_a_row = 0
    db.commit()
    state = _state_response(game, players)
    return {"players": info, **state}


@app.post("/games/{game_id}/play")
def play_move(game_id: int, req: MoveRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    """Play a move in the specified game and return updated state."""
    game = db.get(models.Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    if req.player_id != game.next_player_id:
        raise HTTPException(status_code=409, detail="not_your_turn")
    tiles = db.query(models.PlacedTile).filter_by(game_id=game_id).all()
    players = db.query(models.GamePlayer).filter_by(game_id=game_id).all()
    load_game_state([(t.x, t.y, t.letter) for t in tiles], [p.rack for p in players])
    try:
        score = place_tiles([(p.row, p.col, p.letter.upper(), p.blank) for p in req.placements])
    except ValueError as exc:  # pragma: no cover - validation passthrough
        raise HTTPException(status_code=400, detail=str(exc))
    for p in req.placements:
        tile = models.PlacedTile(
            game_id=game_id,
            player_id=req.player_id,
            x=p.row,
            y=p.col,
            letter=p.letter.upper(),
        )
        db.add(tile)
    player = db.get(models.GamePlayer, req.player_id)
    if player is None or player.game_id != game_id:
        raise HTTPException(status_code=404, detail="Player not found")
    rack_list = list(player.rack)
    for p in req.placements:
        letter = "?" if p.blank else p.letter.upper()
        if letter in rack_list:
            rack_list.remove(letter)
    drawn = draw_tiles(7 - len(rack_list))
    rack_list.extend(drawn)
    player.rack = "".join(rack_list)
    player.score += score
    players_sorted = sorted(players, key=lambda pl: pl.id)
    idx = next(i for i, pl in enumerate(players_sorted) if pl.id == req.player_id)
    game.next_player_id = players_sorted[(idx + 1) % len(players_sorted)].id
    game.passes_in_a_row = 0
    db.commit()

    players, bot_move, bot_score = _maybe_play_bot(game_id, game, db)

    state = _state_response(game, players)
    state["score"] = score
    if bot_move:
        state["bot_move"] = bot_move
        state["bot_score"] = bot_score
    return state


@app.post("/games/{game_id}/exchange")
def exchange_tiles(
    game_id: int, req: ExchangeRequest, db: Session = Depends(get_db)
) -> dict[str, list[str]]:
    """Exchange tiles from the player's rack with new ones."""
    tiles = db.query(models.PlacedTile).filter_by(game_id=game_id).all()
    players = db.query(models.GamePlayer).filter_by(game_id=game_id).all()
    load_game_state([(t.x, t.y, t.letter) for t in tiles], [p.rack for p in players])
    player = db.get(models.GamePlayer, req.player_id)
    if player is None or player.game_id != game_id:
        raise HTTPException(status_code=404, detail="Player not found")
    rack_list = list(player.rack)
    for letter in req.letters:
        up = letter.upper()
        if up not in rack_list:
            raise HTTPException(status_code=400, detail="tile_not_in_rack")
        rack_list.remove(up)
        game_module.bag.append(up)
    random.shuffle(game_module.bag)
    new_letters = draw_tiles(len(req.letters))
    rack_list.extend(new_letters)
    player.rack = "".join(rack_list)
    db.commit()
    return {"letters": new_letters}


@app.post("/games/{game_id}/pass")
def pass_turn(game_id: int, req: PassRequest) -> dict[str, str]:
    """Pass the current turn."""
    return {"status": "passed"}


@app.post("/games/{game_id}/challenge")
def challenge_move(game_id: int, req: ChallengeRequest) -> dict[str, str]:
    """Challenge the previous move (simplified placeholder)."""
    return {"status": "challenge_not_supported"}


@app.post("/games/{game_id}/resign")
def resign_game(
    game_id: int, req: ResignRequest, db: Session = Depends(get_db)
) -> dict[str, str]:
    """Resign from the game."""
    game = db.get(models.Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    game.finished = True
    db.commit()
    return {"status": "resigned"}


@app.get("/games/{game_id}")
def get_game_state(
    game_id: int, player_id: int, db: Session = Depends(get_db)
) -> GameState:
    """Retrieve the current state of a game."""
    tiles = db.query(models.PlacedTile).filter_by(game_id=game_id).all()
    players = db.query(models.GamePlayer).filter_by(game_id=game_id).all()
    game = db.get(models.Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    load_game_state([(t.x, t.y, t.letter) for t in tiles], [p.rack for p in players])
    player = (
        db.query(models.GamePlayer)
        .filter_by(game_id=game_id, id=player_id)
        .first()
    )
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    players, _bot_move, _bot_score = _maybe_play_bot(game_id, game, db)
    tiles = db.query(models.PlacedTile).filter_by(game_id=game_id).all()
    state = _state_response(game, players)
    return GameState(
        rack=list(player.rack),
        tiles=[Tile(row=t.x, col=t.y, letter=t.letter) for t in tiles],
        bag_count=state["bag_count"],
        next_player_id=state["next_player_id"],
        scores=state["scores"],
        passes_in_a_row=state["passes_in_a_row"],
        phase=state["phase"],
    )

