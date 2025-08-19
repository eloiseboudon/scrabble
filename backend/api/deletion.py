from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..deletion import process_due_deletions
from ..models import models
from .auth import get_current_user

router = APIRouter()

GRACE_PERIOD_DAYS = 30


@router.post("/me/deletion-request")
def request_account_deletion(request: Request, db: Session = Depends(get_db)) -> dict:
    user = get_current_user(request, db)
    existing = db.query(models.DeletionRequest).filter_by(user_id=user.id).first()
    if existing and existing.status in {"pending", "grace"}:
        raise HTTPException(status_code=400, detail="Deletion already requested")
    grace_until = datetime.now(timezone.utc) + timedelta(days=GRACE_PERIOD_DAYS)
    dr = models.DeletionRequest(
        user_id=user.id, status="grace", grace_until=grace_until
    )
    db.add(dr)
    db.add(
        models.PrivacyAuditLog(
            event="deletion_requested", subject_id=user.id, details={}
        )
    )
    db.commit()
    return {"status": dr.status, "grace_until": dr.grace_until.isoformat()}


@router.post("/admin/process-deletions")
def trigger_deletion_processing(db: Session = Depends(get_db)) -> dict:
    process_due_deletions(db)
    return {"status": "ok"}
