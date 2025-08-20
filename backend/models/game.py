from datetime import datetime, timezone
from typing import List

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.now(timezone.utc),
        nullable=False,
    )
    max_players: Mapped[int] = mapped_column(nullable=False)
    vs_computer: Mapped[bool] = mapped_column(default=False, nullable=False)
    finished: Mapped[bool] = mapped_column(default=False, nullable=False)
    started: Mapped[bool] = mapped_column(default=False, nullable=False)
    next_player_id: Mapped[int | None] = mapped_column(nullable=True)
    passes_in_a_row: Mapped[int] = mapped_column(default=0, nullable=False)
    phase: Mapped[str] = mapped_column(
        String, default="waiting_players", nullable=False
    )

    __table_args__ = (
        CheckConstraint("max_players >= 2 AND max_players <= 4", name="ck_max_players"),
    )

    players: Mapped[List["GamePlayer"]] = relationship(
        "GamePlayer", back_populates="game"
    )
    tiles: Mapped[List["PlacedTile"]] = relationship(
        "PlacedTile", back_populates="game"
    )
    words: Mapped[List["Word"]] = relationship("Word", back_populates="game")


class GamePlayer(Base):
    __tablename__ = "game_players"

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    is_computer: Mapped[bool] = mapped_column(default=False, nullable=False)
    rack: Mapped[str] = mapped_column(String, nullable=False)
    score: Mapped[int] = mapped_column(default=0, nullable=False)

    game: Mapped["Game"] = relationship("Game", back_populates="players")
    user: Mapped["User"] = relationship("User", back_populates="games")


class PlacedTile(Base):
    __tablename__ = "placed_tiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("game_players.id"), nullable=False
    )
    x: Mapped[int] = mapped_column(nullable=False)
    y: Mapped[int] = mapped_column(nullable=False)
    letter: Mapped[str] = mapped_column(String(1), nullable=False)

    game: Mapped["Game"] = relationship("Game", back_populates="tiles")
    player: Mapped["GamePlayer"] = relationship("GamePlayer")


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("game_players.id"), nullable=False
    )
    word: Mapped[str] = mapped_column(String, nullable=False)
    score: Mapped[int] = mapped_column(nullable=False)

    game: Mapped["Game"] = relationship("Game", back_populates="words")
    player: Mapped["GamePlayer"] = relationship("GamePlayer")
