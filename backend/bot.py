"""Bot logic for Scrabble game.

This module contains the AI logic for the Scrabble bot, including functions to generate
valid moves, find the best word placements, and make intelligent decisions during the game.
"""

from typing import List, Tuple, Optional, Set
from . import game

BOARD_SIZE = game.BOARD_SIZE
DICTIONARY = game.DICTIONARY
LETTER_DISTRIBUTION = game.LETTER_DISTRIBUTION

# Points par lettre
LETTER_POINTS = {letter: points for letter, (_, points) in LETTER_DISTRIBUTION.items()}


def generate_all_words(rack: List[str], prefix: str = "", words: Optional[Set[str]] = None) -> Set[str]:
    """Generate all possible words that can be formed from the rack letters.
    
    Args:
        rack: List of letters available in the rack
        prefix: Current prefix being built (used in recursion)
        words: Set to store found words (used in recursion)
        
    Returns:
        Set of all valid words that can be formed from the rack
    """
    if words is None:
        words = set()
        
    # Convert rack to list for manipulation
    rack_list = list(rack)
    
    # Check if current prefix is a valid word
    if prefix and prefix.lower() in DICTIONARY and len(prefix) > 1:
        words.add(prefix.upper())
    
    # Recursively build words
    for i, letter in enumerate(rack_list):
        # Use the letter in the current position
        new_rack = rack_list[:i] + rack_list[i+1:]
        new_prefix = prefix + letter
        
        # Continue building words with remaining letters
        generate_all_words(new_rack, new_prefix, words)
        
        # Also try with blank tiles (if any) as any letter
        if letter == '?':
            for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                new_rack = rack_list[:i] + rack_list[i+1:]
                new_prefix = prefix + c
                generate_all_words(new_rack, new_prefix, words)
    
    return words


def get_board_letters(board: List[List[str]]) -> List[Tuple[int, int, str]]:
    """Get all letters currently on the board with their positions.
    
    Args:
        board: 2D list representing the game board
        
    Returns:
        List of tuples (row, col, letter) for each letter on the board
    """
    letters = []
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col]:
                letters.append((row, col, board[row][col]))
    return letters


def find_anchor_squares(board: List[List[str]]) -> List[Tuple[int, int, bool]]:
    """Find all anchor squares on the board where a word can be placed.
    
    An anchor square is an empty square adjacent to a letter on the board.
    
    Args:
        board: 2D list representing the game board
        
    Returns:
        List of tuples (row, col, is_horizontal) where words can be placed
    """
    anchors = []
    board_letters = get_board_letters(board)
    
    # If board is empty, return the center square
    if not board_letters:
        center = BOARD_SIZE // 2
        return [(center, center, True), (center, center, False)]
    
    # Check all positions adjacent to existing letters
    for row, col, _ in board_letters:
        # Check all 4 directions
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            r, c = row + dr, col + dc
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and not board[r][c]:
                # Check if this position is already in anchors
                existing = False
                for ar, ac, _ in anchors:
                    if ar == r and ac == c:
                        existing = True
                        break
                if not existing:
                    # Add both horizontal and vertical possibilities
                    anchors.append((r, c, True))  # Horizontal anchor
                    anchors.append((r, c, False))  # Vertical anchor
    
    return anchors


def find_word_extensions(
    board: List[List[str]], 
    row: int, 
    col: int, 
    direction: str
) -> Tuple[str, List[Tuple[int, int]]]:
    """Find the word that would be formed by placing a letter at (row, col).
    
    Args:
        board: 2D list representing the game board
        row: Starting row position
        col: Starting column position
        direction: 'across' or 'down'
        
    Returns:
        Tuple of (word, positions) where word is the complete word that would be formed
        and positions is a list of (row, col) tuples where letters would be placed
    """
    word = ""
    positions = []
    
    # Find the start of the word
    r, c = row, col
    if direction == 'across':
        while c > 0 and board[r][c-1]:
            c -= 1
    else:  # down
        while r > 0 and board[r-1][c]:
            r -= 1
    
    # Build the word and collect positions
    while r < BOARD_SIZE and c < BOARD_SIZE and (board[r][c] or (r == row and c == col)):
        if not board[r][c]:  # This is where we'll place a new letter
            word += "?"  # Placeholder for new letter
            positions.append((r, c))
        else:
            word += board[r][c]
        
        if direction == 'across':
            c += 1
        else:
            r += 1
    
    return word, positions


def is_valid_placement(
    board: List[List[str]], 
    word: str, 
    row: int, 
    col: int, 
    direction: str
) -> Tuple[bool, int, List[Tuple[int, int, str]]]:
    """Check if placing a word at the given position is valid.
    
    Args:
        board: 2D list representing the game board
        word: Word to place
        row: Starting row position
        col: Starting column position
        direction: 'across' or 'down'
        
    Returns:
        Tuple of (is_valid, score, placements) where:
        - is_valid: Boolean indicating if the placement is valid
        - score: Score the move would get (0 if invalid)
        - placements: List of (row, col, letter) tuples for each new letter placed
    """
    # Make a copy of the board to simulate the move
    temp_board = [row[:] for row in board]
    placements = []
    
    # Check if the word fits on the board
    word_len = len(word)
    if direction == 'across':
        if col + word_len > BOARD_SIZE:
            return False, 0, []
    else:  # down
        if row + word_len > BOARD_SIZE:
            return False, 0, []
    
    # Check each letter position
    for i in range(word_len):
        r = row + (i if direction == 'down' else 0)
        c = col + (i if direction == 'across' else 0)
        
        # If the position is empty, we'll place a new letter
        if not temp_board[r][c]:
            # Check if this position is adjacent to existing letters
            has_adjacent = False
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and temp_board[nr][nc]:
                    has_adjacent = True
                    break
            
            # If not adjacent to any existing letters and not the first move, it's invalid
            if not has_adjacent and any(any(cell for cell in row) for row in temp_board):
                return False, 0, []
            
            # Add to placements
            placements.append((r, c, word[i]))
        else:
            # If the position is not empty, the existing letter must match our word
            if temp_board[r][c] != word[i]:
                return False, 0, []
    
    # Check if we're placing at least one new letter
    if not placements:
        return False, 0, []
    
    # Check if the word connects to existing words
    if any(any(cell for cell in row) for row in temp_board):
        connected = False
        for r, c, _ in placements:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and temp_board[nr][nc]:
                    connected = True
                    break
            if connected:
                break
        if not connected:
            return False, 0, []
    
    # Calculate score (simplified version, can be enhanced with bonus squares)
    score = sum(LETTER_POINTS.get(letter, 0) for _, _, letter in placements)
    
    # Bonus for using all 7 letters
    if len(placements) == 7:
        score += 50
    
    return True, score, placements


def generate_best_move(board: List[List[str]], rack: List[str]) -> Tuple[List[Tuple[int, int, str, bool]], int]:
    """Generate the best possible move for the bot.
    
    Args:
        board: 2D list representing the game board
        rack: List of letters in the bot's rack
        
    Returns:
        Tuple of (placements, score) where:
        - placements: List of (row, col, letter, is_blank) tuples for each letter to place
        - score: Score of the move
    """
    # Generate all possible words from the rack
    possible_words = generate_all_words(rack)
    
    # Find all anchor squares where we can place words
    anchors = find_anchor_squares(board)
    
    best_score = -1
    best_placements = []
    
    # Try each word at each anchor position
    for word in possible_words:
        for row, col, is_horizontal in anchors:
            direction = 'across' if is_horizontal else 'down'
            
            # Try placing the word starting at different offsets
            for offset in range(len(word)):
                start_row = row - (offset if not is_horizontal else 0)
                start_col = col - (offset if is_horizontal else 0)
                
                if start_row < 0 or start_col < 0:
                    continue
                
                # Check if the word fits at this position
                is_valid, score, placements = is_valid_placement(
                    board, word, start_row, start_col, direction
                )
                
                if is_valid and score > best_score:
                    best_score = score
                    # Convert to the format expected by the game engine
                    best_placements = [
                        (r, c, letter, False)  # is_blank is always False for now
                        for r, c, letter in placements
                    ]
    
    # If no valid move found, try to exchange tiles if possible
    if best_score == -1 and len(game.bag) >= len(rack):
        # Return empty placements to indicate a pass/exchange
        return [], 0
    
    return best_placements, best_score


def bot_turn(board: List[List[str]], rack: List[str]) -> Tuple[List[Tuple[int, int, str, bool]], int]:
    """Make a move for the bot.
    
    Args:
        board: 2D list representing the game board
        rack: List of letters in the bot's rack
        
    Returns:
        Tuple of (placements, score) where:
        - placements: List of (row, col, letter, is_blank) tuples for each letter to place
        - score: Score of the move (0 for pass/exchange)
    """
    # If it's the first move, place a word horizontally starting from the center
    if not any(any(cell for cell in row) for row in board):
        center = BOARD_SIZE // 2
        word = ''.join(rack[:min(7, len(rack))])
        placements = [
            (center, center + i, letter, False)  # is_blank is always False for now
            for i, letter in enumerate(word)
        ]
        score = sum(LETTER_POINTS.get(letter, 0) for letter in word)
        return placements, score
    
    # Otherwise, find the best move
    return generate_best_move(board, rack)
