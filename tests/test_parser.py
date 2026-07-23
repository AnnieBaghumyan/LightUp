"""Tests for the puzzle text parser."""

from pathlib import Path

import pytest

from lightup import parser

PUZZLES = Path(__file__).resolve().parent.parent / "puzzles"


def test_round_trip():
    text = "2..\n...\n...\n"
    puzzle = parser.parse(text)
    assert parser.to_text(puzzle) == text


def test_thesis_glyphs_are_equivalent():
    # '-' and '*' (used in the Pulles 2021 thesis) mean '.' and '#'.
    ours = parser.parse(".#.\n.1.\n...")
    theirs = parser.parse("-*-\n-1-\n---")
    assert ours.grid == theirs.grid


def test_blank_lines_are_ignored():
    puzzle = parser.parse("\n2..\n\n...\n...\n\n")
    assert puzzle.height == 3 and puzzle.width == 3


def test_ragged_rows_rejected():
    with pytest.raises(ValueError, match="row 1"):
        parser.parse("...\n....\n...")


def test_bad_character_rejected():
    with pytest.raises(ValueError, match="row 1, column 2"):
        parser.parse("...\n..x\n...")


def test_empty_input_rejected():
    with pytest.raises(ValueError, match="no grid lines"):
        parser.parse("\n  \n")


def test_parse_thesis_file():
    puzzle = parser.parse_file(PUZZLES / "thesis7x7.txt")
    assert puzzle.height == 7 and puzzle.width == 7
    # Spot-check cells against Figure 2.1 of the thesis.
    assert puzzle.clue(0, 5) == 0
    assert puzzle.clue(1, 0) == 1
    assert puzzle.clue(1, 4) == 2
    assert puzzle.is_wall(2, 1) and puzzle.clue(2, 1) is None
    assert puzzle.clue(5, 6) == 3
    assert puzzle.clue(6, 1) == 2
    assert puzzle.is_white(3, 3)
