"""FastAPI backend for Scrabble application."""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
SECRET_KEY = os.getenv("SECRET_KEY", "dev_change_me")

app = FastAPI()

# 2) CORS en dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3) SessionMiddleware requis pour Authlib (Google OAuth)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# 4) Importer les routers APRÈS le chargement du .env et les middlewares
from .api import auth, games, health, deletion  # noqa: E402

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(games.router)
app.include_router(deletion.router)
