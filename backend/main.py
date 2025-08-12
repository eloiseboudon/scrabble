"""FastAPI backend for Scrabble application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import games, health, users

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(users.router)
app.include_router(games.router)
