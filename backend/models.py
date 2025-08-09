from datetime import datetime
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    games = relationship("GamePlayer", back_populates="user")


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    max_players = Column(Integer, nullable=False)
    vs_computer = Column(Boolean, default=False, nullable=False)
    finished = Column(Boolean, default=False, nullable=False)
    started = Column(Boolean, default=False, nullable=False)
    next_player_id = Column(Integer, nullable=True)
    passes_in_a_row = Column(Integer, default=0, nullable=False)
    phase = Column(String, default="waiting_players", nullable=False)

    __table_args__ = (
        CheckConstraint("max_players >= 2 AND max_players <= 4", name="ck_max_players"),
    )

    players = relationship("GamePlayer", back_populates="game")
    tiles = relationship("PlacedTile", back_populates="game")
    words = relationship("Word", back_populates="game")


class GamePlayer(Base):
    __tablename__ = "game_players"

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_computer = Column(Boolean, default=False, nullable=False)
    rack = Column(String, nullable=False)
    score = Column(Integer, default=0, nullable=False)

    game = relationship("Game", back_populates="players")
    user = relationship("User", back_populates="games")


class PlacedTile(Base):
    __tablename__ = "placed_tiles"

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    letter = Column(String(1), nullable=False)

    game = relationship("Game", back_populates="tiles")


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    word = Column(String, nullable=False)
    score = Column(Integer, nullable=False)

    game = relationship("Game", back_populates="words")
