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


@router.post("/register")
def register(req: AuthRequest, db: Session = Depends(get_db)) -> dict[str, int]:
    """Create a new user and return its identifier."""
    if db.query(models.User).filter_by(username=req.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed = hashlib.sha256(req.password.encode()).hexdigest()
    user = models.User(username=req.username, hashed_password=hashed)
    db.add(user)
    db.commit()
    return {"user_id": user.id}


@router.post("/login")
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


@router.get("/users/by-username")
def get_user_by_username(
    username: str, db: Session = Depends(get_db)
) -> UserLookupResponse:
    """Retrieve a user's identifier by their username."""
    user = db.query(models.User).filter_by(username=username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    return UserLookupResponse(user_id=user.id)
