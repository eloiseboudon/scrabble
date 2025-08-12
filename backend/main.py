"""FastAPI backend for Scrabble application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .api import auth, games, health

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware required for OAuth (stores auth state)
app.add_middleware(SessionMiddleware, secret_key=auth.SECRET_KEY)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(games.router)
