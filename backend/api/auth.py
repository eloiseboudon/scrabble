import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

ENV = os.getenv("ENV", "dev")
PROD_DOMAIN = os.getenv("PROD_DOMAIN", ".ton-domaine")
DEV_DOMAIN = "localhost"

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

router = APIRouter()


class AuthRequest(BaseModel):
    email: EmailStr
    password: str


class UserManager:
    """Simple user manager for validations and hooks."""

    def __init__(self, db: Session):
        self.db = db

    async def validate_password(self, password: str) -> None:
        if len(password) < 3:
            raise HTTPException(status_code=400, detail="Password too short")

    async def validate_email(self, email: EmailStr) -> None:
        existing = self.db.query(models.User).filter_by(username=email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")

    async def on_after_register(self, user: models.User) -> None:
        # Placeholder hook for post-registration actions
        return None

    async def on_after_login(self, user: models.User) -> None:
        # Placeholder hook for post-login actions
        return None


def _cookie_params() -> dict:
    domain = PROD_DOMAIN if ENV == "prod" else DEV_DOMAIN
    secure = ENV == "prod"
    samesite = "none" if ENV == "prod" else "lax"
    return {
        "httponly": True,
        "secure": secure,
        "samesite": samesite,
        "domain": domain,
    }


def create_token(data: dict, expires: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def set_access_cookie(response: Response, token: str) -> None:
    params = _cookie_params()
    response.set_cookie(
        "access_token",
        token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        **params,
    )


def set_refresh_cookie(response: Response, token: str) -> None:
    params = _cookie_params()
    response.set_cookie(
        "refresh_token",
        token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        **params,
    )


def clear_cookies(response: Response) -> None:
    params = _cookie_params()
    response.set_cookie("access_token", "", max_age=0, **params)
    response.set_cookie("refresh_token", "", max_age=0, **params)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token"
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    user = db.get(models.User, int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


@router.post("/auth/register")
async def register(req: AuthRequest, db: Session = Depends(get_db)) -> dict[str, int]:
    manager = UserManager(db)
    await manager.validate_email(req.email)
    await manager.validate_password(req.password)
    hashed = pwd_context.hash(req.password)
    user = models.User(username=req.email, hashed_password=hashed)
    db.add(user)
    db.commit()
    await manager.on_after_register(user)
    return {"user_id": user.id}


@router.post("/auth/login")
async def login(
    req: AuthRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> dict[str, int]:
    user = db.query(models.User).filter_by(username=req.email).first()
    if not user or not pwd_context.verify(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    manager = UserManager(db)
    await manager.on_after_login(user)
    access = create_token(
        {"sub": str(user.id)}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh = create_token(
        {"sub": str(user.id), "type": "refresh"},
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    set_access_cookie(response, access)
    set_refresh_cookie(response, refresh)
    return {"user": user}


@router.post("/auth/refresh")
async def refresh(
    response: Response, request: Request, db: Session = Depends(get_db)
) -> dict[str, int]:
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token"
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise JWTError("Invalid token type")
        user_id = int(payload.get("sub"))
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from exc
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    access = create_token(
        {"sub": str(user.id)}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_token(
        {"sub": str(user.id), "type": "refresh"},
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    set_access_cookie(response, access)
    set_refresh_cookie(response, refresh_token)
    return {"user_id": user.id}


@router.post("/auth/logout")
async def logout(response: Response) -> dict[str, str]:
    clear_cookies(response)
    return {"detail": "logged_out"}


@router.get("/auth/me")
async def me(request: Request, db: Session = Depends(get_db)) -> dict[str, str | int]:
    return {"user": get_current_user(request, db)}


@router.get("/auth/google/authorize")
async def google_authorize() -> dict[str, str]:
    """Redirect user to Google's OAuth2 consent screen (placeholder)."""
    return {"detail": "redirect_to_google"}


@router.get("/auth/google/callback")
async def google_callback() -> dict[str, str]:
    """Handle Google OAuth2 callback (placeholder)."""
    return {"detail": "google_callback"}
