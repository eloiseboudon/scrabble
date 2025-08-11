"""Core game logic for Scrabble rules."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

BOARD_SIZE = 15

# ---------------------------------------------------------------------------
# Letter distribution and values (French Scrabble)
# ---------------------------------------------------------------------------

# Each entry: letter -> (count, points)
LETTER_DISTRIBUTION: dict[str, tuple[int, int]] = {
    "A": (9, 1),
    "B": (2, 3),
    "C": (2, 3),
    "D": (3, 2),
    "E": (15, 1),
    "F": (2, 4),
    "G": (2, 2),
    "H": (2, 4),
    "I": (8, 1),
    "J": (1, 8),
    "K": (1, 10),
    "L": (5, 1),
    "M": (3, 2),
    "N": (6, 1),
    "O": (6, 1),
    "P": (2, 3),
    "Q": (1, 8),
    "R": (6, 1),
    "S": (6, 1),
    "T": (6, 1),
    "U": (6, 1),
    "V": (2, 4),
    "W": (1, 10),
    "X": (1, 10),
    "Y": (1, 10),
    "Z": (1, 10),
    "?": (2, 0),  # Jokers
}

LETTER_POINTS = {ltr: pts for ltr, (_, pts) in LETTER_DISTRIBUTION.items()}

# Load dictionary
DICTIONARY = set(Path("backend/ods8.txt").read_text().splitlines())

# ---------------------------------------------------------------------------
# Board bonuses configuration
# ---------------------------------------------------------------------------


def _empty_board(value: str = "") -> List[List[str]]:
    return [[value for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


BONUS: List[List[str]] = _empty_board()

# Triple Word (TW)
for r, c in [
    (0, 0),
    (0, 7),
    (0, 14),
    (7, 0),
    (7, 14),
    (14, 0),
    (14, 7),
    (14, 14),
]:
    BONUS[r][c] = "TW"

# Double Word (DW)
for r, c in [
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
    (10, 10),
    (11, 11),
    (12, 12),
    (13, 13),
    (1, 13),
    (2, 12),
    (3, 11),
    (4, 10),
    (10, 4),
    (11, 3),
    (12, 2),
    (13, 1),
]:
    BONUS[r][c] = "DW"

# Triple Letter (TL)
for r, c in [
    (1, 5),
    (1, 9),
    (5, 1),
    (5, 5),
    (5, 9),
    (5, 13),
    (9, 1),
    (9, 5),
    (9, 9),
    (9, 13),
    (13, 5),
    (13, 9),
]:
    BONUS[r][c] = "TL"

# Double Letter (DL)
for r, c in [
    (0, 3),
    (0, 11),
    (2, 6),
    (2, 8),
    (3, 0),
    (3, 7),
    (3, 14),
    (6, 2),
    (6, 6),
    (6, 8),
    (6, 12),
    (7, 3),
    (7, 11),
    (8, 2),
    (8, 6),
    (8, 8),
    (8, 12),
    (11, 0),
    (11, 7),
    (11, 14),
    (12, 6),
    (12, 8),
    (14, 3),
    (14, 11),
]:
    BONUS[r][c] = "DL"

# Center star
BONUS[7][7] = "CENTER"

# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------

bag: List[str] = []
board: List[List[str | None]] = []
first_move = True


def reset_game() -> None:
    """Reset bag, board and first-move flag."""
    global bag, board, first_move
    bag = []
    for letter, (count, _) in LETTER_DISTRIBUTION.items():
        bag.extend([letter] * count)
    random.shuffle(bag)
    board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    first_move = True


reset_game()

# ---------------------------------------------------------------------------
# Loading persisted game state
# ---------------------------------------------------------------------------


def load_game_state(
    tiles: Iterable[Tuple[int, int, str]], racks: Iterable[str]
) -> None:
    """Populate board and bag from persisted *tiles* and *racks*."""
    global bag, board, first_move
    reset_game()
    counts = {ltr: count for ltr, (count, _) in LETTER_DISTRIBUTION.items()}
    board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for r, c, letter in tiles:
        board[r][c] = letter
        counts[letter.upper()] -= 1
    for rack in racks:
        for letter in rack:
            counts[letter.upper()] -= 1
    bag = []
    for letter, (total, _) in LETTER_DISTRIBUTION.items():
        bag.extend([letter] * counts[letter])
    random.shuffle(bag)
    first_move = not list(tiles)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def draw_tiles(n: int) -> List[str]:
    """Draw up to *n* tiles from the bag."""
    draw = bag[:n]
    del bag[:n]
    return draw


class Placement(Tuple[int, int, str, bool]):
    row: int
    col: int
    letter: str
    blank: bool


def _word_from_board(
    r: int, c: int, dr: int, dc: int
) -> Tuple[str, List[Tuple[int, int]]]:
    """Read a word from the board starting at (r,c) moving (dr,dc)."""
    letters = []
    coords = []
    while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] is not None:
        letters.append(board[r][c])
        coords.append((r, c))
        r += dr
        c += dc
    return "".join(letters), coords


def _score_word(
    coords: List[Tuple[int, int]], new_tiles: Iterable[Tuple[int, int]]
) -> int:
    """Compute score for the word covering *coords*.

    *new_tiles* are coordinates of tiles placed this turn."""
    new_set = set(new_tiles)
    word_multiplier = 1
    score = 0
    for r, c in coords:
        letter = board[r][c]
        letter_score = 0 if letter.islower() else LETTER_POINTS.get(letter.upper(), 0)
        if (r, c) in new_set:
            bonus = BONUS[r][c]
            if bonus == "DL":
                letter_score *= 2
            elif bonus == "TL":
                letter_score *= 3
            elif bonus in {"DW", "CENTER"}:
                word_multiplier *= 2
            elif bonus == "TW":
                word_multiplier *= 3
        score += letter_score
    return score * word_multiplier


def place_tiles(placements: List[Tuple[int, int, str, bool]]) -> int:
    """Place tiles on the board according to *placements*.

    Each placement is (row, col, letter, blank).
    Returns the score for the move or raises ValueError if the move is invalid."""
    global first_move

    if not placements:
        raise ValueError("No tiles placed")

    # ----- 1) Alignement sur une ligne ou une colonne -----
    rows = {r for r, _, _, _ in placements}
    cols = {c for _, c, _, _ in placements}
    if len(rows) != 1 and len(cols) != 1:
        raise ValueError("Tiles must be in a single row or column")
    horizontal = len(rows) == 1

    # ----- 2) Vérif cases libres + poser temporairement -----
    # (on pose pour pouvoir lire les mots ensuite)
    # NB: on suppose que 'board', 'BOARD_SIZE' existent
    used_positions = set()
    for r, c, letter, is_blank in placements:
        if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE):
            raise ValueError("Placement out of board")
        if board[r][c] is not None:
            raise ValueError("Cell already occupied")
        # on stocke la lettre posée (minuscule si joker)
        board[r][c] = letter.lower() if is_blank else letter.upper()
        used_positions.add((r, c))

    # ----- 3) Continuité (pas de trous) + connexion au plateau -----
    # Continuité sur la ligne/colonne
    if horizontal:
        r = next(iter(rows))
        cmin = min(c for _, c, _, _ in placements)
        cmax = max(c for _, c, _, _ in placements)
        # il faut qu'entre cmin..cmax, au moins les emplacements posés ou existants remplissent la chaîne
        for c in range(cmin, cmax + 1):
            if board[r][c] is None:
                # trou -> invalide
                # revert
                for rr, cc in used_positions:
                    board[rr][cc] = None
                raise ValueError("Tiles must be contiguous")
    else:
        c = next(iter(cols))
        rmin = min(r for r, _, _, _ in placements)
        rmax = max(r for r, _, _, _ in placements)
        for r in range(rmin, rmax + 1):
            if board[r][c] is None:
                for rr, cc in used_positions:
                    board[rr][cc] = None
                raise ValueError("Tiles must be contiguous")

    # Connexion au plateau (hors premier coup)
    if first_move:
        if (7, 7) not in used_positions:
            for rr, cc in used_positions:
                board[rr][cc] = None
            raise ValueError("First move must cover the center square")

    else:
        # au moins un voisin existant
        connected = False
        for r, c, _, _ in placements:
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = r + dr, c + dc
                if (
                    0 <= rr < BOARD_SIZE
                    and 0 <= cc < BOARD_SIZE
                    and board[rr][cc] is not None
                    and (rr, cc) not in used_positions
                ):
                    connected = True
                    break
            if connected:
                break
        if not connected:
            for rr, cc in used_positions:
                board[rr][cc] = None
            raise ValueError("Move must connect to existing tiles")

    # ----- 4) Déterminer le mot principal -----
    if horizontal:
        r = next(iter(rows))
        # remonter à gauche
        c_start = min(c for _, c, _, _ in placements)
        while c_start > 0 and board[r][c_start - 1] is not None:
            c_start -= 1
        main_word, main_coords = _word_from_board(r, c_start, 0, 1)
    else:
        c = next(iter(cols))
        r_start = min(r for r, _, _, _ in placements)
        while r_start > 0 and board[r_start - 1][c] is not None:
            r_start -= 1
        main_word, main_coords = _word_from_board(r_start, c, 1, 0)

    # ----- 5) Valider le mot principal -----
    if main_word.upper() not in DICTIONARY:
        for rr, cc in used_positions:
            board[rr][cc] = None
        raise ValueError("Main word not in dictionary")

    # ----- 6) Construire et valider tous les mots secondaires -----
    # (le cœur du correctif : on vérifie les mots croisés formés par chaque tuile posée)
    cross_coords_list: List[List[Tuple[int, int]]] = []
    for r, c, _, _ in placements:
        if horizontal:
            # le mot secondaire est vertical à cette colonne
            rr = r
            # si pas de voisin vertical => pas de mot secondaire
            above = rr > 0 and board[rr - 1][c] is not None
            below = rr + 1 < BOARD_SIZE and board[rr + 1][c] is not None
            if not (above or below):
                continue
            # remonter
            r0 = rr
            while r0 > 0 and board[r0 - 1][c] is not None:
                r0 -= 1
            word, coords = _word_from_board(r0, c, 1, 0)
        else:
            # le mot secondaire est horizontal à cette ligne
            cc = c
            left = cc > 0 and board[r][cc - 1] is not None
            right = cc + 1 < BOARD_SIZE and board[r][cc + 1] is not None
            if not (left or right):
                continue
            c0 = cc
            while c0 > 0 and board[r][c0 - 1] is not None:
                c0 -= 1
            word, coords = _word_from_board(r, c0, 0, 1)

        # On ne garde que les "mots" de longueur >= 2
        if len(coords) > 1:
            if word.upper() not in DICTIONARY:
                # revert et échec si un seul mot secondaire n'est pas valide
                for rr, cc in used_positions:
                    board[rr][cc] = None
                raise ValueError(f"Invalid cross word: {word}")
            cross_coords_list.append(coords)

    # ----- 7) Calcul du score : mot principal + tous les mots secondaires -----
    total = _score_word(main_coords, used_positions)
    for coords in cross_coords_list:
        total += _score_word(coords, used_positions)
    # Bingo: 50 points si 7 tuiles posées en un seul coup
    if len(placements) == 7:
        total += 50
    # ----- 8) Fin de coup OK -----
    # (ici tu peux conserver ton éventuel bonus de scrabble/bingo si tu l'avais ailleurs)
    first_move = False
    return total


def bot_turn(rack: List[str]) -> Optional[Tuple[List[Tuple[int, int, str, bool]], int]]:
    """Make a move for the bot.

    Args:
        rack: List of letters in the bot's rack

    Returns:
        Tuple of (placements, score) where:
        - placements: List of (row, col, letter, is_blank) tuples for each letter to place
        - score: Score of the move (0 for pass/exchange)
        If no valid move is possible, returns None.
    """
    try:
        from . import bot as bot_module

        return bot_module.bot_turn(board, rack)
    except Exception as e:
        print(f"Error in bot_turn: {e}")
        return None


def generate_valid_moves(board, rack, dictionary):
    """Generate all valid moves for the given rack and board state.

    Args:
        board: 2D list representing the current game board
        rack: List of letters in the player's rack
        dictionary: Set of valid words

    Returns:
        List of valid moves, where each move is a tuple of (placements, score)
    """
    # This is a placeholder implementation.
    # In a real implementation, you would generate all possible valid moves
    # by trying to place the rack letters on the board in all possible positions
    # and checking if they form valid words.

    # For now, we'll return an empty list to indicate no valid moves found
    # The bot will handle this case by passing or exchanging tiles
    return []
