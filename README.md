# Scrabble Application

This project hosts a minimal Scrabble application with:

- **Backend**: Python using FastAPI.
- **Frontend**: Vue 3 (loaded from CDN).
- **Database**: PostgreSQL (not yet integrated).

The first iteration displays a Scrabble board locally.

## Setup

### Backend
1. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Run the server:
   ```bash
   uvicorn backend.main:app --reload
   ```
3. Visit `http://localhost:8000/health` for a health check.

### Frontend
Open `frontend/index.html` in a browser. It uses Vue via CDN and displays the Scrabble board.

### Notes
- The ODS8 dictionary will be integrated in a later iteration.
- Ensure PostgreSQL is running for future database features.
