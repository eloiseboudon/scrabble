import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

from backend import bot  # type: ignore


def test_is_valid_placement_rejects_invalid_cross_word():
    board = [[None for _ in range(bot.BOARD_SIZE)] for _ in range(bot.BOARD_SIZE)]
    board[7][7] = "A"
    original_dict = bot.DICTIONARY.copy()
    try:
        bot.DICTIONARY = {"BB"}
        is_valid, _score, _placements = bot.is_valid_placement(board, "BB", 6, 7, "down")
        assert not is_valid
    finally:
        bot.DICTIONARY = original_dict

