import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Tuple

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from .. import models
from ..database import SessionLocal, get_db

# =========================================================
# Settings (lit à partir de .env, avec compatibilité anciens noms)
# =========================================================
SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or os.getenv("JWT_LIFETIME_MINUTES", "15")
)
REFRESH_TOKEN_EXPIRE_DAYS = int(
    os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")
    or os.getenv("JWT_REFRESH_LIFETIME_DAYS", "7")
)
SHORT_REFRESH_TOKEN_DAYS = 7

ENV = os.getenv("ENV", "dev")  # 'dev' | 'prod'
# Préférence : COOKIE_DOMAIN (si fourni), sinon PROD_DOMAIN
COOKIE_DOMAIN_ENV = os.getenv("COOKIE_DOMAIN", "").strip()
PROD_DOMAIN = os.getenv("PROD_DOMAIN", "").strip()
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()

# =========================================================
# Sécurité / hashing
# =========================================================
# Préfère argon2; fallback bcrypt si l'extra n'est pas installé
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

router = APIRouter()

# OAuth (enregistrement lazy pour éviter les problèmes d'ordre de chargement)
oauth = OAuth()


def _is_google_registered() -> bool:
    """Return True if the Google OAuth client is already registered."""
    return "google" in oauth._registry


def ensure_google_registered() -> bool:
    """Enregistre Google au runtime si les env vars existent."""
    if _is_google_registered():
        return True
    # <-- Relire l'env ICI (et ne pas se fier aux variables de module)
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        return False
    oauth.register(
        name="google",
        client_id=client_id,
        client_secret=client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    return True


@router.get("/auth/google/status")
def google_status() -> dict:
    ready_after_ensure = ensure_google_registered()
    return {
        "configured": _is_google_registered(),
        "ready_after_ensure": ready_after_ensure,
        "has_client_id": bool(GOOGLE_CLIENT_ID),
        "has_client_secret": bool(GOOGLE_CLIENT_SECRET),
        "backend_url": BACKEND_URL,
        "frontend_url": FRONTEND_URL,
    }


# =========================================================
# Helpers cookies
# =========================================================
def _cookie_params() -> dict:
    secure = ENV == "prod"
    samesite = "none" if ENV == "prod" else "lax"
    params = {
        "httponly": True,
        "secure": secure,
        "samesite": samesite,
    }
    # En dev : ne PAS mettre de domain pour localhost (meilleure compatibilité).
    domain_to_use = COOKIE_DOMAIN_ENV or PROD_DOMAIN
    if ENV == "prod" and domain_to_use and domain_to_use.lower() != "localhost":
        params["domain"] = domain_to_use
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


def set_refresh_cookie(
    response: Response, token: str, *, days: int = REFRESH_TOKEN_EXPIRE_DAYS
) -> None:
    params = _cookie_params()
    response.set_cookie(
        "refresh_token",
        token,
        max_age=days * 24 * 3600,
        path="/",
        **params,
    )


def clear_cookies(response: Response) -> None:
    common = {"path": "/"}
    domain_to_use = COOKIE_DOMAIN_ENV or PROD_DOMAIN
    if ENV == "prod" and domain_to_use and domain_to_use.lower() != "localhost":
        common["domain"] = domain_to_use
    response.delete_cookie("access_token", **common)
    response.delete_cookie("refresh_token", **common)


# =========================================================
# Helpers JWT
# =========================================================
def _utcnow() -> datetime:
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


# =========================================================
# Refresh tokens en base (rotation stricte)
# models.RefreshToken requis (table: refresh_tokens)
# =========================================================
def _issue_refresh(
    db: Session, user_id: int, days: int = REFRESH_TOKEN_EXPIRE_DAYS
) -> str:
    rt = models.RefreshToken(
        user_id=user_id,
        revoked=False,
        expires_at=_utcnow() + timedelta(days=days),
    )
    db.add(rt)
    db.commit()
    db.refresh(rt)
    # Token signé avec jti (id de la table)
    token = create_token(
        {"sub": str(user_id), "type": "refresh"},
        timedelta(days=days),
        jti=str(rt.id),
    )
    return token


def _revoke_refresh(db: Session, jti: int) -> None:
    obj = db.get(models.RefreshToken, jti)
    if obj and not obj.revoked:
        obj.revoked = True
        obj.revoked_at = _utcnow()
        db.add(obj)
        db.commit()


def _validate_refresh(db: Session, token: str) -> Tuple[int, int, models.RefreshToken]:
    """Retourne (user_id, jti, obj) si le refresh est valide, sinon lève HTTP 401."""
    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise JWTError("Invalid token type")
        user_id = int(payload.get("sub"))
        jti = int(payload.get("jti"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from exc

    rt = db.get(models.RefreshToken, jti)
    if not rt or rt.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    if rt.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked"
        )
    expires = rt.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires <= _utcnow():
        # Soft revoke expiré
        rt.revoked = True
        rt.revoked_at = _utcnow()
        db.add(rt)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired"
        )
    return user_id, jti, rt


# =========================================================
# Dépendance utilisateur courant (via access_token)
# =========================================================
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


# =========================================================
# Schémas / logique métier (register/login/me)
# =========================================================
class AuthRequest(BaseModel):
    """Payload login/register : username OU email + password."""

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


class LoginRequest(AuthRequest):
    remember_me: bool = False


class UserResponse(BaseModel):
    user_id: int
    email: str  # on renvoie username comme 'email' par compatibilité
    display_name: str | None = None
    avatar_url: str | None = None
    color_palette: str | None = None


class PaletteUpdate(BaseModel):
    palette: str


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

    def on_after_register(self, user: models.User) -> None:  # hooks
        return None

    def on_after_login(self, user: models.User) -> None:  # hooks
        return None


def register(req: AuthRequest, db: Session) -> int:
    manager = UserManager(db)
    username = req.identifier
    manager.validate_username(username)
    manager.validate_password(req.password)
    hashed = pwd_context.hash(req.password)
    user = models.User(username=username, hashed_password=hashed)
    # Champs optionnels
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


def me_lookup(email_or_username: str, db: Session | None = None) -> UserResponse:
    """Lookup direct (utilisé aussi par des tests unitaires)."""
    own = False
    if db is None:
        db = SessionLocal()
        own = True
    try:
        user = db.query(models.User).filter_by(username=email_or_username).first()
        if user is None:
            raise HTTPException(status_code=404, detail="user_not_found")
        return UserResponse(user_id=user.id, email=user.username)
    finally:
        if own:
            db.close()


# =========================================================
# Routes REST
# =========================================================
@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register_endpoint(
    req: AuthRequest, db: Session = Depends(get_db)
) -> dict[str, int]:
    user_id = register(req, db)
    return {"user_id": user_id}


@router.post("/auth/login")
def login_endpoint(
    req: LoginRequest, response: Response, db: Session = Depends(get_db)
) -> dict[str, int]:
    user_id = login(req, db)
    # Access (court)
    access = create_token(
        {"sub": str(user_id)}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    set_access_cookie(response, access)
    # Refresh (durée variable)
    days = REFRESH_TOKEN_EXPIRE_DAYS if req.remember_me else SHORT_REFRESH_TOKEN_DAYS
    refresh = _issue_refresh(db, user_id, days=days)
    set_refresh_cookie(response, refresh, days=days)
    # Hook post-login
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
    user_id, jti, rt = _validate_refresh(db, token)
    # Rotation stricte : révoque l'ancien, émet un nouveau
    _revoke_refresh(db, jti)
    new_access = create_token(
        {"sub": str(user_id)}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    ttl_days = int((rt.expires_at - rt.created_at).total_seconds() // 86400) or 1
    new_refresh = _issue_refresh(db, user_id, days=ttl_days)
    set_access_cookie(response, new_access)
    set_refresh_cookie(response, new_refresh, days=ttl_days)
    return {"user_id": user_id}


@router.post("/auth/logout")
def logout_endpoint(
    request: Request, response: Response, db: Session = Depends(get_db)
) -> dict[str, str]:
    # Si un refresh est présent, on le révoque
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
def me_endpoint(request: Request, db: Session = Depends(get_db)) -> UserResponse:
    user = get_current_user(request, db)
    return UserResponse(
        user_id=user.id,
        email=user.username,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        color_palette=user.color_palette,
    )


@router.post("/auth/me/palette")
def update_palette(
    req: PaletteUpdate, request: Request, db: Session = Depends(get_db)
) -> dict[str, str]:
    user = get_current_user(request, db)
    user.color_palette = req.palette
    db.add(user)
    db.commit()
    return {"color_palette": user.color_palette}


@router.post("/auth/me/avatar")
async def update_avatar(
    request: Request,
    db: Session = Depends(get_db),
    file: UploadFile | None = File(None),
    choice: str | None = Form(None),
) -> dict[str, str]:
    user = get_current_user(request, db)
    if file is not None:
        uploads_dir = (
            Path(__file__).resolve().parent.parent / "uploads" / "avatars"
        )
        uploads_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(file.filename).suffix or ".png"
        filename = f"user_{user.id}{ext}"
        file_path = uploads_dir / filename
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        user.avatar_url = f"/uploads/avatars/{filename}"
    elif choice:
        allowed = {f"default{i}.svg" for i in range(1, 6)}
        if choice not in allowed:
            raise HTTPException(status_code=400, detail="Invalid avatar choice")
        user.avatar_url = f"/static/avatars/{choice}"
    else:
        raise HTTPException(status_code=400, detail="No avatar provided")
    db.add(user)
    db.commit()
    return {"avatar_url": user.avatar_url}

# Backward compatible alias for tests expecting `me`
me = me_lookup


# =========================================================
# Google OAuth (lazy-config)
# =========================================================
@router.get("/auth/google/authorize")
async def google_authorize(request: Request):
    if not ensure_google_registered():
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    redirect_uri = f"{BACKEND_URL}/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    if not ensure_google_registered():
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    # 1) Échange code -> token
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {e.error}") from e
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"OAuth exchange failed: {e}"
        ) from e

    # 2) Tenter userinfo via Authlib (userinfo endpoint découvert)
    userinfo = None
    try:
        resp = await oauth.google.get("userinfo", token=token)
        if resp is not None and getattr(resp, "status_code", None) == 200:
            data = resp.json()
            if isinstance(data, dict) and "email" in data:
                userinfo = data
    except Exception:
        pass

    # 3) Fallback 1: appel direct à l’endpoint OIDC standard
    if not userinfo:
        import httpx

        access_token = token.get("access_token")
        if access_token:
            for url in (
                "https://openidconnect.googleapis.com/v1/userinfo",
                "https://www.googleapis.com/oauth2/v3/userinfo",
            ):
                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        r = await client.get(
                            url, headers={"Authorization": f"Bearer {access_token}"}
                        )
                    if r.status_code == 200 and "email" in r.json():
                        userinfo = r.json()
                        break
                except Exception:
                    continue

    # 4) Fallback 2: décoder l’ID token pour extraire l’email (si présent)
    if not userinfo:
        try:
            parsed = await oauth.google.parse_id_token(request, token)
            if isinstance(parsed, dict) and "email" in parsed:
                userinfo = parsed
        except Exception:
            pass

    if not userinfo or "email" not in userinfo:
        # Affiche les infos utiles pour debug
        raise HTTPException(status_code=400, detail="Unable to fetch Google user info")

    email = userinfo["email"].lower()
    display_name = userinfo.get("name")

    # 5) find-or-create user
    user = db.query(models.User).filter_by(username=email).first()
    if not user:
        user = models.User(
            username=email, hashed_password=pwd_context.hash(os.urandom(16).hex())
        )
        if hasattr(user, "is_active"):
            user.is_active = True
        if hasattr(user, "is_verified"):
            user.is_verified = True
        if hasattr(user, "display_name") and display_name:
            user.display_name = display_name
        if hasattr(user, "created_at"):
            user.created_at = _utcnow()
        if hasattr(user, "updated_at"):
            user.updated_at = _utcnow()
        db.add(user)
        db.commit()
        db.refresh(user)

    # 6) Cookies + redirect front
    access = create_token(
        {"sub": str(user.id)}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh = (
        _issue_refresh(db, user.id)
        if "_issue_refresh" in globals()
        else create_token(
            {"sub": str(user.id), "type": "refresh"},
            timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    response = RedirectResponse(url=FRONTEND_URL)
    set_access_cookie(response, access)
    set_refresh_cookie(response, refresh)
    return response


# ---- Route DEBUG (à retirer en prod) ----
@router.get("/auth/google/callback-debug")
async def google_callback_debug(request: Request):
    if not ensure_google_registered():
        return {"error": "Google OAuth not configured"}

    data = {"stage": "start"}
    try:
        token = await oauth.google.authorize_access_token(request)
        data["token_keys"] = list(token.keys())
        data["has_access_token"] = bool(token.get("access_token"))
        data["has_id_token"] = bool(token.get("id_token"))

        # Essai 1 : userinfo via Authlib
        try:
            resp = await oauth.google.get("userinfo", token=token)
            data["userinfo_status"] = getattr(resp, "status_code", None)
            data["userinfo_body"] = (
                resp.json() if getattr(resp, "status_code", None) == 200 else resp.text
            )
        except Exception as e:
            data["userinfo_error"] = str(e)

        # Essai 2 : userinfo via httpx + Authorization: Bearer
        try:
            import httpx

            access_token = token.get("access_token")
            if access_token:
                async with httpx.AsyncClient(timeout=10) as client:
                    r = await client.get(
                        "https://openidconnect.googleapis.com/v1/userinfo",
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                data["userinfo_direct_status"] = r.status_code
                data["userinfo_direct_body"] = (
                    r.json() if r.status_code == 200 else r.text
                )
        except Exception as e:
            data["userinfo_direct_error"] = str(e)

        # Essai 3 : parse_id_token
        try:
            parsed = await oauth.google.parse_id_token(request, token)
            data["parsed_id_token_keys"] = (
                list(parsed.keys())
                if isinstance(parsed, dict)
                else type(parsed).__name__
            )
        except Exception as e:
            data["parse_id_token_error"] = str(e)

    except Exception as e:
        data["fatal_error"] = str(e)

    return data
