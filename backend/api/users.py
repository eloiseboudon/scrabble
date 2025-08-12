import hashlib

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter()


class AuthRequest(BaseModel):
    username: str
    password: str


class UserLookupResponse(BaseModel):
    user_id: int


@router.post("/auth/register")
def register(req: AuthRequest, db: Session = Depends(get_db)) -> dict[str, int]:
    """Create a new user and return its identifier."""
    if db.query(models.User).filter_by(username=req.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed = hashlib.sha256(req.password.encode()).hexdigest()
    user = models.User(username=req.username, hashed_password=hashed)
    db.add(user)
    db.commit()
    return {"user_id": user.id}


@router.post("/auth/login")
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


@router.post("/auth/logout")
def logout(req: AuthRequest, db: Session = Depends(get_db)) -> dict[str, int]:
    """Logout a user and clear cookie"""
    return {"user_id": req.user_id}


@router.get("/auth/google/authorize")
def google_authorize(req: AuthRequest, db: Session = Depends(get_db)):
    """(redirige vers Google)"""
    return {"user_id": req.user_id}


@router.get("/auth/google/callback")
def google_callback(req: AuthRequest, db: Session = Depends(get_db)):
    """(callback OAuth, création/connexion user)"""
    return {"user_id": req.user_id}


@router.get("/auth/me")
def get_user_by_username(
    username: str, db: Session = Depends(get_db)
) -> UserLookupResponse:
    """Retrieve a user's identifier by their username."""
    user = db.query(models.User).filter_by(username=username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    return UserLookupResponse(user_id=user.id)
