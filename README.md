# Scrabble Application

This project hosts a minimal Scrabble application with:

- **Backend**: Python using FastAPI.
- **Frontend**: Vue 3 (loaded from CDN).
- **Database**: PostgreSQL (not yet integrated).

The first iteration displays a Scrabble board locally.

## Setup

### Backend
1. Set up the virtual environment and install dependencies:
   ```bash
   make install
   ```
2. Run the server:
   ```bash
   make backend
   ```
3. Visit `http://localhost:8000/health` for a health check.

### Frontend
Serve the static files and open the Scrabble board:
```bash
make frontend
```
Then visit `http://localhost:5173` in a browser.

### Notes
- The ODS8 dictionary will be integrated in a later iteration.
- Ensure PostgreSQL is running for future database features.
