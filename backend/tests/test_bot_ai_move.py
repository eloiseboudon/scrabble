import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

from backend import bot  # type: ignore


def test_bot_finds_move_with_dictionary_and_rack():
    board = [[None for _ in range(bot.BOARD_SIZE)] for _ in range(bot.BOARD_SIZE)]
    board[7][7] = "N"
    board[7][8] = "U"
    board[7][9] = "E"
    original_dict = bot.DICTIONARY
    original_by_len = bot.DICTIONARY_BY_LENGTH
    try:
        bot.DICTIONARY = {"NUE", "ET"}
        bot.DICTIONARY_BY_LENGTH = {3: ["NUE"], 2: ["ET"]}
        placements, score = bot.bot_turn(board, list("TAAAAAA"))
        assert score > 0
        assert (8, 9, "T", False) in placements
    finally:
        bot.DICTIONARY = original_dict
        bot.DICTIONARY_BY_LENGTH = original_by_len
