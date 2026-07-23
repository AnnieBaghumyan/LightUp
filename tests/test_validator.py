"""Tests for the rule validator, using small hand-checked puzzles.

The 7x7 puzzle and its solution come from Figure 2.1 of Pulles (2021),
"Analysis of Akari" — a published, trusted reference solution.
"""

from pathlib import Path

from lightup import parser
from lightup.board import lit_cells
from lightup.validator import (check_partial, check_solution, involved_cells,
                               is_solved)

PUZZLES = Path(__file__).resolve().parent.parent / "puzzles"

# Bulb positions of the published solution to thesis7x7.txt.
THESIS_SOLUTION = {(0, 0), (1, 3), (2, 4), (3, 5),
                   (4, 2), (4, 6), (5, 1), (5, 5), (6, 0), (6, 6)}


def kinds(violations):
    return {v.kind for v in violations}


# ----- full solutions --------------------------------------------------------

def test_thesis_solution_is_valid():
    puzzle = parser.parse_file(PUZZLES / "thesis7x7.txt")
    assert is_solved(puzzle, THESIS_SOLUTION)


def test_corner2_solution_is_valid():
    puzzle = parser.parse_file(PUZZLES / "corner2.txt")
    assert is_solved(puzzle, {(0, 1), (1, 0), (2, 2)})


def test_tiny3x3_solution_is_valid():
    puzzle = parser.parse_file(PUZZLES / "tiny3x3.txt")
    assert is_solved(puzzle, {(0, 1), (1, 0), (2, 2)})


def test_missing_bulb_is_detected():
    puzzle = parser.parse_file(PUZZLES / "thesis7x7.txt")
    broken = THESIS_SOLUTION - {(6, 6)}
    violations = check_solution(puzzle, broken)
    # Cells in the bottom row go dark and the '3' clue at (5,6) loses a bulb.
    assert "cell_unlit" in kinds(violations)
    assert "clue_unmet" in kinds(violations)
    assert not is_solved(puzzle, broken)


# ----- partial-state checks --------------------------------------------------

def test_valid_partial_state_has_no_violations():
    puzzle = parser.parse_file(PUZZLES / "thesis7x7.txt")
    assert check_partial(puzzle, {(0, 0), (1, 3)}) == []


def test_bulbs_seeing_each_other():
    puzzle = parser.parse("...\n...\n...")
    violations = check_partial(puzzle, {(0, 0), (0, 2)})
    assert kinds(violations) == {"bulbs_see_each_other"}
    assert violations[0].cells == ((0, 0), (0, 2))


def test_wall_blocks_line_of_sight():
    puzzle = parser.parse(".#.\n...\n...")
    # Same row as above, but the wall stands between the bulbs: legal.
    assert check_partial(puzzle, {(0, 0), (0, 2)}) == []


def test_clue_exceeded():
    puzzle = parser.parse("0.\n..")
    violations = check_partial(puzzle, {(0, 1)})
    assert "clue_exceeded" in kinds(violations)


def test_clue_unsatisfiable_from_the_start():
    # A '4' clue in a corner has only two white neighbors: impossible.
    puzzle = parser.parse_file(PUZZLES / "unsolvable3x3.txt")
    violations = check_partial(puzzle, set())
    assert "clue_unsatisfiable" in kinds(violations)


def test_clue_unsatisfiable_after_bad_placement():
    # The '1' clue at (0,0) has neighbors (0,1) and (1,0).  The two bulbs
    # below do not break any rule between themselves, but the bulb at (2,1)
    # lights (0,1) and the bulb at (1,2) lights (1,0) — so neither neighbor
    # can take a bulb anymore and the clue can never be satisfied.
    puzzle = parser.parse("1..\n...\n...")
    violations = check_partial(puzzle, {(2, 1), (1, 2)})
    assert kinds(violations) == {"clue_unsatisfiable"}


def test_bulb_on_wall_is_reported():
    puzzle = parser.parse_file(PUZZLES / "thesis7x7.txt")
    violations = check_partial(puzzle, {(2, 1)})  # (2,1) is a wall
    assert "bulb_not_on_white" in kinds(violations)


def test_involved_cells_filters_by_kind():
    puzzle = parser.parse("...\n...\n...")
    violations = check_solution(puzzle, {(0, 0), (0, 2)})
    # Only the clashing bulbs, not every unlit cell.
    cells = involved_cells(violations, kinds={"bulbs_see_each_other"})
    assert cells == {(0, 0), (0, 2)}
    # Unfiltered, the unlit cells are included too.
    assert (1, 1) in involved_cells(violations)


# ----- lighting geometry -----------------------------------------------------

def test_lit_cells_stop_at_walls():
    puzzle = parser.parse(".#.\n...\n...")
    lit = lit_cells(puzzle, {(0, 0)})
    # The bulb lights itself, down its column, but not past the wall at (0,1).
    assert lit == {(0, 0), (1, 0), (2, 0)}
