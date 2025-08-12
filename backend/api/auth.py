import os
from datetime import datetime, timedelta, timezone
from typing import Optional

# Google OAuth (Authlib)
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from .. import models
from ..database import SessionLocal, get_db

# ================== Settings ==================
SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

ENV = os.getenv("ENV", "dev")  # 'dev' | 'prod'
PROD_DOMAIN = os.getenv("PROD_DOMAIN", ".ton-domaine")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# ================== Security ==================
# Prefer argon2; fallback to bcrypt if unavailable (install passlib[argon2])
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

router = APIRouter()

# Initialize OAuth (requires SessionMiddleware in main app)
oauth = OAuth()
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


# ================== Schemas ==================
class AuthRequest(BaseModel):
    """Login/Register payload.
    Accepts either username or email for convenience.
    """

    username: str | None = None
    email: EmailStr | None = None
    password: str

    @property
    def identifier(self) -> str:
        if self.username:
            return self.username
        if self.email:
            return str(self.email)
        raise HTTPException(status_code=400, detail="Username or email required")


class UserResponse(BaseModel):
    user_id: int
    email: str  # here 'email' actually carries username for backward compat


# ================== Cookie helpers ==================
def _cookie_params() -> dict:
    secure = ENV == "prod"
    samesite = "none" if ENV == "prod" else "lax"
    params = {
        "httponly": True,
        "secure": secure,
        "samesite": samesite,
    }
    if ENV == "prod":
        params["domain"] = PROD_DOMAIN
    return params


def set_access_cookie(response: Response, token: str) -> None:
    params = _cookie_params()
    response.set_cookie(
        "access_token",
        token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        **params,
    )


def set_refresh_cookie(response: Response, token: str) -> None:
    params = _cookie_params()
    response.set_cookie(
        "refresh_token",
        token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/",
        **params,
    )


def clear_cookies(response: Response) -> None:
    common = {"path": "/"}
    if ENV == "prod":
        common["domain"] = PROD_DOMAIN
    response.delete_cookie("access_token", **common)
    response.delete_cookie("refresh_token", **common)


# ================== JWT helpers ==================
def _utcnow():
    return datetime.now(timezone.utc)


def create_token(data: dict, expires: timedelta, *, jti: Optional[str] = None) -> str:
    to_encode = data.copy()
    now = _utcnow()
    to_encode.update(
        {
            "iat": int(now.timestamp()),
            "exp": int((now + expires).timestamp()),
            "type": to_encode.get("type", "access"),
        }
    )
    if jti:
        to_encode["jti"] = jti
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


# ================== Refresh Token Store (DB) ==================
def _issue_refresh(db: Session, user_id: int) -> str:
    # Create DB record
    rt = models.RefreshToken(
        user_id=user_id,
        revoked=False,
        expires_at=_utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(rt)
    db.commit()
    db.refresh(rt)
    # Create signed token with jti
    token = create_token(
        {"sub": str(user_id), "type": "refresh"},
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        jti=str(rt.id),
    )
    return token


def _revoke_refresh(db: Session, jti: int) -> None:
    obj = db.get(models.RefreshToken, jti)
    if obj:
        obj.revoked = True
        obj.revoked_at = _utcnow()
        db.add(obj)
        db.commit()


def _validate_refresh(db: Session, token: str) -> int:
    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise JWTError("Invalid token type")
        user_id = int(payload.get("sub"))
        jti = int(payload.get("jti"))
    except Exception as exc:  # includes ValueError, JWTError
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from exc

    # Check DB state
    rt = db.get(models.RefreshToken, jti)
    if not rt or rt.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    if rt.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked"
        )
    if rt.expires_at <= _utcnow():
        # Soft revoke expired
        rt.revoked = True
        rt.revoked_at = _utcnow()
        db.add(rt)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired"
        )
    return user_id, jti


# ================== Current user dependency ==================
def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token"
        )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise JWTError("Wrong token type")
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
    if getattr(user, "is_active", True) is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User disabled"
        )
    return user


# ================== Business funcs (tests & routes) ==================
class UserManager:
    def __init__(self, db: Session):
        self.db = db

    def validate_password(self, password: str) -> None:
        if len(password) < 8:
            raise HTTPException(status_code=400, detail="Password too short")

    def validate_username(self, username: str) -> None:
        existing = self.db.query(models.User).filter_by(username=username).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")

    def on_after_register(self, user: models.User) -> None:
        return None

    def on_after_login(self, user: models.User) -> None:
        return None


class AuthRequest(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str

    @property
    def identifier(self) -> str:
        if self.username:
            return self.username
        if self.email:
            return str(self.email)
        raise HTTPException(status_code=400, detail="Username or email required")


def register(req: AuthRequest, db: Session) -> int:
    manager = UserManager(db)
    username = req.identifier
    manager.validate_username(username)
    manager.validate_password(req.password)
    hashed = pwd_context.hash(req.password)
    user = models.User(username=username, hashed_password=hashed)
    if hasattr(user, "is_active") and getattr(user, "is_active") is None:
        user.is_active = True
    if hasattr(user, "created_at") and getattr(user, "created_at") is None:
        user.created_at = _utcnow()
    if hasattr(user, "updated_at"):
        user.updated_at = _utcnow()

    db.add(user)
    db.commit()
    db.refresh(user)
    manager.on_after_register(user)
    return user.id


def login(req: AuthRequest, db: Session) -> int:
    username = req.identifier
    user = db.query(models.User).filter_by(username=username).first()
    if not user or not pwd_context.verify(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    if getattr(user, "is_active", True) is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User disabled"
        )
    return user.id


def me(email_or_username: str, db: Session | None = None):
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True
    try:
        user = db.query(models.User).filter_by(username=email_or_username).first()
        if user is None:
            raise HTTPException(status_code=404, detail="user_not_found")
        return {"user_id": user.id, "email": user.username}
    finally:
        if own_session:
            db.close()


# ================== Routes ==================
@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register_endpoint(
    req: AuthRequest, db: Session = Depends(get_db)
) -> dict[str, int]:
    user_id = register(req, db)
    return {"user_id": user_id}


@router.post("/auth/login")
def login_endpoint(
    req: AuthRequest, response: Response, db: Session = Depends(get_db)
) -> dict[str, int]:
    user_id = login(req, db)
    # Access
    access = create_token(
        {"sub": str(user_id)}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    set_access_cookie(response, access)
    # Refresh (with DB record + JTI)
    refresh = _issue_refresh(db, user_id)
    set_refresh_cookie(response, refresh)
    # hook
    user = db.get(models.User, user_id)
    UserManager(db).on_after_login(user)
    return {"user_id": user_id}


@router.post("/auth/refresh")
def refresh_endpoint(
    response: Response, request: Request, db: Session = Depends(get_db)
) -> dict[str, int]:
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token"
        )
    # Validate and get user_id + jti
    user_id, jti = _validate_refresh(db, token)
    # Revoke the old refresh
    _revoke_refresh(db, jti)
    # Issue a new refresh and access (rotation)
    new_access = create_token(
        {"sub": str(user_id)}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    new_refresh = _issue_refresh(db, user_id)
    set_access_cookie(response, new_access)
    set_refresh_cookie(response, new_refresh)
    return {"user_id": user_id}


@router.post("/auth/logout")
def logout_endpoint(
    request: Request, response: Response, db: Session = Depends(get_db)
) -> dict[str, str]:
    # If a refresh cookie exists, revoke it
    token = request.cookies.get("refresh_token")
    if token:
        try:
            payload = decode_token(token)
            if payload.get("type") == "refresh" and "jti" in payload:
                _revoke_refresh(db, int(payload["jti"]))
        except Exception:
            pass
    clear_cookies(response)
    return {"detail": "logged_out"}


@router.get("/auth/me")
def me_endpoint(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return {"user_id": user.id, "email": user.username}


# ================== Google OAuth (Authlib) ==================
@router.get("/auth/google/authorize")
async def google_authorize(request: Request):
    if "google" not in oauth:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    redirect_uri = f"{BACKEND_URL}/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    if "google" not in oauth:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    try:
        token = await oauth.google.authorize_access_token(request)  # exchanges 'code'
    except OAuthError as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {e.error}") from e

    # Get user info (via ID token or userinfo endpoint)
    userinfo = token.get("userinfo")
    if not userinfo:
        # Try parsing ID token
        try:
            userinfo = await oauth.google.parse_id_token(request, token)
        except Exception:
            pass
    if not userinfo or "email" not in userinfo:
        raise HTTPException(status_code=400, detail="Unable to fetch Google user info")

    email = userinfo["email"].lower()
    display_name = userinfo.get("name")

    # Find or create user
    user = db.query(models.User).filter_by(username=email).first()
    if not user:
        # Create a passwordless user (OAuth only)
        user = models.User(
            username=email, hashed_password=pwd_context.hash(os.urandom(16).hex())
        )
        if hasattr(user, "is_active") and getattr(user, "is_active") is None:
            user.is_active = True
        if hasattr(user, "is_verified"):
            try:
                user.is_verified = True
            except Exception:
                pass
        if hasattr(user, "display_name") and display_name:
            try:
                user.display_name = display_name
            except Exception:
                pass
        if hasattr(user, "created_at") and getattr(user, "created_at") is None:
            user.created_at = _utcnow()
        if hasattr(user, "updated_at"):
            user.updated_at = _utcnow()
        db.add(user)
        db.commit()
        db.refresh(user)

    # Login: set cookies (access + refresh rotation)
    access = create_token(
        {"sub": str(user.id)}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh = _issue_refresh(db, user.id)

    response = RedirectResponse(url=f"{FRONTEND_URL}")
    set_access_cookie(response, access)
    set_refresh_cookie(response, refresh)
    return response
