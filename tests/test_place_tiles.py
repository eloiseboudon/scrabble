import sys
from pathlib import Path

# Ensure repository root is on the Python path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import backend.game as g

def test_single_tile_vertical_word():
    g.reset_game()
    g.place_tiles([(7, 7, 'H', False), (7, 8, 'A', False)])
    score = g.place_tiles([(8, 7, 'E', False)])
    assert score > 0
    assert g.board[7][7] == 'H'
    assert g.board[8][7] == 'E'
