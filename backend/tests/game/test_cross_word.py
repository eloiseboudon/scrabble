import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

from backend import bot  # type: ignore


def test_build_move_rejects_invalid_cross_word():
    """build_move_from_state should reject placements forming invalid cross words."""

    # Create an empty board with a single existing tile ``S`` to the left of where
    # the move will be placed.  Placing the letters "LI" horizontally starting at
    # column 7 would create the cross word ``SL`` which is not present in the
    # dictionary.
    board = bot.Board()
    board.get(7, 6).letter = "S"

    # Minimal dictionary only containing the main word ``LI``.
    trie = bot.Trie()
    trie.insert("LI")

    placements = [(7, 7, "L", False), (7, 8, "I", False)]
    mv = bot.build_move_from_state(
        board, row=7, anchor_col=7, placed=placements, vertical=False, trie=trie
    )

    # The move should be rejected because the cross word "SL" is invalid.
    assert mv is None
