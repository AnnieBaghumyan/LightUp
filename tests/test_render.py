"""Tests for the terminal renderer (ASCII mode, exact snapshots)."""

from pathlib import Path

from lightup import parser
from lightup.render import render

PUZZLES = Path(__file__).resolve().parent.parent / "puzzles"


def test_ascii_render_empty_board():
    puzzle = parser.parse_file(PUZZLES / "corner2.txt")
    expected = "\n".join([
        "    0 1 2",
        "  0 2 . .",
        "  1 . . .",
        "  2 . . .",
    ])
    assert render(puzzle, unicode=False, color=False) == expected


def test_ascii_render_with_bulbs_and_light():
    puzzle = parser.parse_file(PUZZLES / "corner2.txt")
    bulbs = {(0, 1), (1, 0), (2, 2)}
    expected = "\n".join([
        "    0 1 2",
        "  0 2 B +",
        "  1 B + +",
        "  2 + + B",
    ])
    assert render(puzzle, bulbs, unicode=False, color=False) == expected


def test_unicode_and_color_modes_run():
    # No exact snapshot for the fancy mode; just make sure it produces the
    # expected glyphs and ANSI reset codes without crashing.
    puzzle = parser.parse_file(PUZZLES / "corner2.txt")
    picture = render(puzzle, {(0, 1)})
    assert "◉" in picture
    assert "\033[0m" in picture
