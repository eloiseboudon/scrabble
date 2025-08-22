"""FastAPI backend for Scrabble application."""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
SECRET_KEY = os.getenv("SECRET_KEY", "dev_change_me")

app = FastAPI()

# Configure CORS
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    FRONTEND_URL,
    "http://app-scrabble.tulip-saas.fr:8001",
    "http://app-scrabble.tulip-saas.fr:8081",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# 3) SessionMiddleware requis pour Authlib (Google OAuth)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Static files for uploaded avatars
uploads_dir = Path(__file__).parent / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# 4) Importer les routers APRÈS le chargement du .env et les middlewares
from .api import auth, deletion, games, health  # noqa: E402

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(games.router)
app.include_router(deletion.router)
