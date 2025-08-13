"""Utilities to process user deletion and anonymization."""
from datetime import datetime, timezone
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from . import models

ANON_NAME = "Joueur anonyme"


def anonymize_user_data(db: Session, user_id: int) -> None:
    """Anonymize game-related data for a user."""
    gps = db.execute(
        select(models.GamePlayer).where(models.GamePlayer.user_id == user_id)
    ).scalars().all()
    for gp in gps:
        if not gp.display_name or gp.display_name.strip() == "":
            gp.display_name = f"{ANON_NAME} #{gp.id}"
        gp.user_id = None
    db.flush()
    db.execute(delete(models.RefreshToken).where(models.RefreshToken.user_id == user_id))


def hard_delete_user(db: Session, user_id: int) -> None:
    """Remove identifying information from the user."""
    user = db.get(models.User, user_id)
    if not user:
        return
    user.username = f"deleted-user-{user.id}"
    user.display_name = None
    user.avatar_url = None
    user.hashed_password = ""
    user.deleted_at = datetime.now(timezone.utc)


def process_due_deletions(db: Session) -> None:
    """Process all deletion requests whose grace period has expired."""
    now = datetime.now(timezone.utc)
    due = db.execute(
        select(models.DeletionRequest).where(
            models.DeletionRequest.status.in_(["grace", "pending"]),
            models.DeletionRequest.grace_until <= now,
        )
    ).scalars().all()
    for dr in due:
        dr.status = "processing"
        anonymize_user_data(db, dr.user_id)
        hard_delete_user(db, dr.user_id)
        dr.status = "done"
        dr.processed_at = now
        db.add(
            models.PrivacyAuditLog(
                event="hard_deleted",
                subject_id=dr.user_id,
                details={"request_id": dr.id},
            )
        )
    db.commit()
