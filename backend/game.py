from __future__ import annotations

"""Core game logic for Scrabble rules."""

from pathlib import Path
import random
from typing import Iterable, List, Tuple

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
    (0, 0), (0, 7), (0, 14),
    (7, 0), (7, 14),
    (14, 0), (14, 7), (14, 14),
]:
    BONUS[r][c] = "TW"

# Double Word (DW)
for r, c in [
    (1, 1), (2, 2), (3, 3), (4, 4),
    (10, 10), (11, 11), (12, 12), (13, 13),
    (1, 13), (2, 12), (3, 11), (4, 10),
    (10, 4), (11, 3), (12, 2), (13, 1),
]:
    BONUS[r][c] = "DW"

# Triple Letter (TL)
for r, c in [
    (1, 5), (1, 9),
    (5, 1), (5, 5), (5, 9), (5, 13),
    (9, 1), (9, 5), (9, 9), (9, 13),
    (13, 5), (13, 9),
]:
    BONUS[r][c] = "TL"

# Double Letter (DL)
for r, c in [
    (0, 3), (0, 11),
    (2, 6), (2, 8),
    (3, 0), (3, 7), (3, 14),
    (6, 2), (6, 6), (6, 8), (6, 12),
    (7, 3), (7, 11),
    (8, 2), (8, 6), (8, 8), (8, 12),
    (11, 0), (11, 7), (11, 14),
    (12, 6), (12, 8),
    (14, 3), (14, 11),
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

def load_game_state(tiles: Iterable[Tuple[int, int, str]], racks: Iterable[str]) -> None:
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


def _word_from_board(r: int, c: int, dr: int, dc: int) -> Tuple[str, List[Tuple[int, int]]]:
    """Read a word from the board starting at (r,c) moving (dr,dc)."""
    letters = []
    coords = []
    while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] is not None:
        letters.append(board[r][c])
        coords.append((r, c))
        r += dr
        c += dc
    return "".join(letters), coords


def _score_word(coords: List[Tuple[int, int]], new_tiles: Iterable[Tuple[int, int]]) -> int:
    """Compute score for the word covering *coords*.

    *new_tiles* are coordinates of tiles placed this turn."""
    new_set = set(new_tiles)
    word_multiplier = 1
    score = 0
    for r, c in coords:
        letter = board[r][c]
        letter_score = LETTER_POINTS.get(letter.upper(), 0)
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

    rows = {r for r, _, _, _ in placements}
    cols = {c for _, c, _, _ in placements}
    if len(rows) != 1 and len(cols) != 1:
        raise ValueError("Tiles must be in a single row or column")
    horizontal = len(rows) == 1
    if len(placements) == 1:
        r, c, _, _ = placements[0]
        horizontal = (
            (c > 0 and board[r][c - 1] is not None)
            or (c < BOARD_SIZE - 1 and board[r][c + 1] is not None)
        )

    for r, c, letter, _ in placements:
        if board[r][c] is not None:
            raise ValueError("Cell already occupied")
        board[r][c] = letter if letter != "?" else None  # temp placeholder

    # Determine word start
    if horizontal:
        row = next(iter(rows))
        cols_sorted = sorted(c for _, c, _, _ in placements)
        c_start = cols_sorted[0]
        while c_start > 0 and board[row][c_start - 1] is not None:
            c_start -= 1
        word, coords = _word_from_board(row, c_start, 0, 1)
    else:
        col = next(iter(cols))
        rows_sorted = sorted(r for r, _, _, _ in placements)
        r_start = rows_sorted[0]
        while r_start > 0 and board[r_start - 1][col] is not None:
            r_start -= 1
        word, coords = _word_from_board(r_start, col, 1, 0)

    if word.upper() not in DICTIONARY:
        # revert placements
        for r, c, _, _ in placements:
            board[r][c] = None
        raise ValueError("Main word not in dictionary")

    # Build set of new tile coords
    new_coords = [(r, c) for r, c, _, _ in placements]

    # Check connectivity / first move rules
    if first_move:
        if (7, 7) not in new_coords:
            for r, c, _, _ in placements:
                board[r][c] = None
            raise ValueError("First move must cover the center square")
        first_move = False
    else:
        if not any(
            (r > 0 and board[r - 1][c] is not None)
            or (r < BOARD_SIZE - 1 and board[r + 1][c] is not None)
            or (c > 0 and board[r][c - 1] is not None)
            or (c < BOARD_SIZE - 1 and board[r][c + 1] is not None)
            for r, c in new_coords
        ):
            for r, c, _, _ in placements:
                board[r][c] = None
            raise ValueError("Move must connect to existing tiles")

    # Resolve jokers (blanks) and finalize board letters
    for r, c, letter, blank in placements:
        board[r][c] = letter.upper() if not blank else letter.lower()

    total_score = _score_word(coords, new_coords)

    # Cross words
    for r, c, letter, blank in placements:
        if horizontal:
            # vertical cross word
            r_start = r
            while r_start > 0 and board[r_start - 1][c] is not None:
                r_start -= 1
            word, coords_cross = _word_from_board(r_start, c, 1, 0)
        else:
            c_start = c
            while c_start > 0 and board[r][c_start - 1] is not None:
                c_start -= 1
            word, coords_cross = _word_from_board(r, c_start, 0, 1)
        if len(coords_cross) > 1:
            if word.upper() not in DICTIONARY:
                for r2, c2, _, _ in placements:
                    board[r2][c2] = None
                raise ValueError(f"Invalid cross word: {word}")
            total_score += _score_word(coords_cross, [(r, c)])

    if len(placements) == 7:
        total_score += 50

    return total_score
