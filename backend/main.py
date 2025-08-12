"""FastAPI backend for Scrabble application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import auth, games, health

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(games.router)
