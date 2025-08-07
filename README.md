# Scrabble Application

This project provides a minimal Scrabble setup:

- **Backend**: Python FastAPI serving a word-validation endpoint backed by a subset of the ODS8 dictionary.
- **Frontend**: Vue 3 rendering the official 15×15 Scrabble board with bonus squares and a draggable rack of seven random letters.
- **Database**: PostgreSQL (placeholder for future use).

## Setup

### Backend
1. Create the virtual environment and install dependencies:
   ```bash
   make install
   ```
2. Start the FastAPI server:
   ```bash
   make backend
   ```
3. Health check: `http://localhost:8000/health`
4. Validate a word: `http://localhost:8000/validate?word=PYTHON`

### Frontend
Serve the static files and open the Scrabble interface:
```bash
make frontend
```
Then visit `http://localhost:5173` in a browser.

- The 15×15 board displays double/triple word and letter squares plus the centre star.
- Drag a letter tile from the rack and drop it onto an empty cell.
- Use the input box and **Valider** button to check a word against the backend.

### Notes
- `backend/ods8.txt` contains a small subset of the ODS8 word list for demonstration purposes.
- Ensure PostgreSQL is available if you plan to extend the project with database features.
