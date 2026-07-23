"""Tests for the naive backtracking baseline.

Correctness is always judged by the validator (any valid solution passes),
never by comparing against one known answer — generated puzzles may have
several legitimate solutions.
"""

from pathlib import Path

from lightup import parser
from lightup.backtracking import solve
from lightup.generator import DIFFICULTY, generate
from lightup.validator import is_solved

PUZZLES = Path(__file__).resolve().parent.parent / "puzzles"


def test_solves_the_fixture_puzzles():
    for name in ["tiny3x3.txt", "corner2.txt", "thesis7x7.txt"]:
        puzzle = parser.parse_file(PUZZLES / name)
        result = solve(puzzle, timeout_s=30)
        assert result.solved and not result.timed_out, name
        assert is_solved(puzzle, result.bulbs), name


def test_reports_unsolvable():
    puzzle = parser.parse_file(PUZZLES / "unsolvable3x3.txt")
    result = solve(puzzle, timeout_s=10)
    assert not result.solved and not result.timed_out
    assert result.bulbs == set()


def test_thesis_puzzle_is_unique():
    # Published puzzles have exactly one solution; asking for up to two and
    # exhausting the search must find exactly one.
    puzzle = parser.parse_file(PUZZLES / "thesis7x7.txt")
    result = solve(puzzle, max_solutions=2, timeout_s=60)
    assert result.solved and not result.timed_out
    assert len(result.solutions) == 1


def test_open_board_has_many_solutions():
    puzzle = parser.parse("...\n...\n...")
    result = solve(puzzle, max_solutions=50, timeout_s=10)
    assert len(result.solutions) > 1
    for bulbs in result.solutions:
        assert is_solved(puzzle, bulbs)


def test_solves_generated_puzzles():
    for seed in range(5):
        for level in ["easy", "medium"]:
            puzzle, _ = generate(7, 7, seed=seed, **DIFFICULTY[level])
            result = solve(puzzle, timeout_s=30)
            assert result.solved, f"{level}, seed {seed}"
            assert is_solved(puzzle, result.bulbs)


def test_stats_and_determinism():
    puzzle = parser.parse_file(PUZZLES / "thesis7x7.txt")
    a = solve(puzzle, timeout_s=30)
    b = solve(puzzle, timeout_s=30)
    assert a.stats.nodes > 0
    # Same puzzle, same fixed order -> identical search effort.
    assert (a.stats.nodes, a.stats.conflicts, a.stats.backtracks) == \
           (b.stats.nodes, b.stats.conflicts, b.stats.backtracks)


def test_observer_sees_a_consistent_story():
    puzzle = parser.parse_file(PUZZLES / "corner2.txt")
    events = []
    solve(puzzle, observer=lambda ev, cell, bulbs: events.append(ev),
          timeout_s=10)
    kinds = set(events)
    assert "place" in kinds and "solution" in kinds
    # Every removal must follow at least as many placements.
    assert events.count("remove") <= events.count("place")