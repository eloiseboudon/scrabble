from typing import List
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class OAuthAccount(Base):
    """OAuth account linked to a user."""
    __tablename__ = "oauth_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="cascade"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[str] = mapped_column(String(320), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="oauth_accounts")


class User(TimestampMixin, Base):
    """Application user."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120))
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(30), default="player", nullable=False)

    oauth_accounts: Mapped[List[OAuthAccount]] = relationship(
        "OAuthAccount", cascade="all, delete-orphan", back_populates="user"
    )
    games: Mapped[List["GamePlayer"]] = relationship(
        "GamePlayer", back_populates="user"
    )
