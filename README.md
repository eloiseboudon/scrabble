# Scrabble Application

This project hosts a minimal Scrabble application with:

- **Backend**: Python using FastAPI, exposing a word validation endpoint based on the ODS8 dictionary.
- **Frontend**: Vue 3 (loaded from CDN) using a `Grid.vue` component to render the board.
- **Database**: PostgreSQL (not yet integrated).

The frontend displays a Scrabble board and a rack of seven letters that can be placed onto the grid. Words can be validated against the dictionary via the backend.

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
4. Validate a word:
   - `http://localhost:8000/validate?word=PYTHON`

### Frontend
Serve the static files and open the Scrabble board:
```bash
make frontend
```
Then visit `http://localhost:5173` in a browser. Click a letter from the rack and then a cell to place it. Use the input and "Valider" button to check a word with the backend.

### Notes
- `backend/ods8.txt` contains a small subset of the ODS8 word list for demonstration.
- Ensure PostgreSQL is running for future database features.
