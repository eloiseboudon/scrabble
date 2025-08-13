import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

from backend import game  # type: ignore


def test_single_tile_extends_vertical_word() -> None:
    game.load_game_state([(10, 5, "T"), (11, 5, "U")], [])
    total, words = game.place_tiles([(12, 5, "E", False)])
    assert words[0][0] == "TUE"
    assert total > 0
