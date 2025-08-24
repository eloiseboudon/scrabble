# Scrabble Application

This project provides a minimal Scrabble setup:

- **Backend**: Python FastAPI serving a word-validation endpoint backed by a subset of the ODS8 dictionary.
- **Frontend**: Vue 3 rendering the official 15×15 Scrabble board with bonus squares and a draggable rack of seven random letters.
- **Database**: PostgreSQL (placeholder for future use) (Homebrew local).

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
3. Health check: `http://localhost:5173/health`
4. Validate a word: `http://localhost:5173/validate?word=PYTHON`

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
- `backend/ods8.txt` contains the ODS8 word list for demonstration purposes.
- Ensure PostgreSQL is available if you plan to extend the project with database features.

## Règles du jeu

### 🎯 Objectif
Obtenir le plus grand nombre de points en formant des mots sur une grille de 15×15 cases à l'aide de lettres tirées aléatoirement.

### 🎲 Matériel
- Plateau de 15×15 cases.
- 102 jetons : 100 lettres avec points et 2 jokers valant 0 point.
- Un sac pour le tirage et des chevalets pour les joueurs.

### 👥 Joueurs
De 2 à 4 joueurs (ou équipes). Chaque joueur commence avec 7 lettres tirées du sac.

### 🧠 Déroulement
1. **Premier mot** : doit passer par l'étoile centrale et peut être horizontal ou vertical.
2. **Tours suivants** : à chaque tour un joueur peut poser des lettres pour former un mot valide, passer, ou échanger des lettres (si le sac contient au moins 7 lettres). Les mots doivent être continus, adjacents à un mot existant et présents dans l'ODS8.

### 🧮 Comptage des points
- Valeur des lettres :
  - 1 point : A, E, I, L, N, O, R, S, T, U
  - 2 points : D, G, M
  - 3 points : B, C, P
  - 4 points : F, H, V
  - 8 points : J, Q
  - 10 points : K, W, X, Y, Z
- Bonus de cases : LD (lettre×2), LT (lettre×3), MD (mot×2), MT (mot×3).
- Bonus Scrabble : +50 points si les 7 lettres du chevalet sont jouées.

### 📕 Vérification des mots
Un mot peut être contesté. S'il n'est pas dans l'ODS8, le coup est annulé et les lettres reprises.

### 🧾 Fin de partie
La partie s'arrête lorsque le sac est vide et qu'un joueur n'a plus de lettres, après 6 tours blancs consécutifs ou par abandon. Chaque joueur soustrait la valeur de ses lettres restantes ; le joueur qui a terminé ajoute cette somme à son score.

### 🧩 Cas particuliers
- Tous les mots formés doivent être valides.
- Il est possible de prolonger un mot existant si le nouveau mot est valide.
- Pluriels et formes conjuguées sont autorisés s'ils apparaissent dans l'ODS8.

### 🏆 Variante Duplicate - A faire
En mode Duplicate, tous les joueurs jouent avec les mêmes lettres et seul le meilleur coup est retenu pour le plateau. Le gagnant est celui qui totalise le plus de points.
