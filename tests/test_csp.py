"""Tests for the smart backtracking variants (forward checking / full
inference).  As always: correctness is judged by the validator, never by
comparing to one known answer."""

from pathlib import Path

from lightup import parser
from lightup.generator import DIFFICULTY, generate
from lightup.solvers.backtracking import solve as naive_solve
from lightup.solvers.csp import solve_forward, solve_full
from lightup.validator import is_solved

PUZZLES = Path(__file__).resolve().parent.parent / "puzzles"
VARIANTS = [("forward checking", solve_forward),
            ("full inference", solve_full)]


def test_variants_solve_the_fixture_puzzles():
    for name in ["tiny3x3.txt", "corner2.txt", "thesis7x7.txt"]:
        puzzle = parser.parse_file(PUZZLES / name)
        for label, solve in VARIANTS:
            result = solve(puzzle, timeout_s=30)
            assert result.solved and not result.timed_out, (name, label)
            assert is_solved(puzzle, result.bulbs), (name, label)


def test_variants_reject_unsolvable():
    puzzle = parser.parse_file(PUZZLES / "unsolvable3x3.txt")
    for label, solve in VARIANTS:
        result = solve(puzzle, timeout_s=10)
        assert not result.solved and not result.timed_out, label


def test_variants_solve_generated_puzzles():
    for seed in range(5):
        for level in ["easy", "medium", "hard"]:
            puzzle, _ = generate(7, 7, seed=seed, **DIFFICULTY[level])
            for label, solve in VARIANTS:
                result = solve(puzzle, timeout_s=30)
                assert result.solved, (level, seed, label)
                assert is_solved(puzzle, result.bulbs), (level, seed, label)


def test_inference_beats_the_naive_baseline():
    # The whole point: on the same puzzle, inference needs far fewer
    # search decisions (much of the board is derived, not guessed).
    puzzle = parser.parse_file(PUZZLES / "thesis7x7.txt")
    naive = naive_solve(puzzle, timeout_s=30)
    full = solve_full(puzzle, timeout_s=30)
    assert full.solved and naive.solved
    assert full.stats.nodes < naive.stats.nodes
    assert full.stats.propagations > 0
    # Forward checking should also not be worse than naive on nodes.
    fc = solve_forward(puzzle, timeout_s=30)
    assert fc.solved and fc.stats.nodes <= naive.stats.nodes


def test_static_ordering_ablation_runs():
    from lightup.solvers.csp import solve
    puzzle = parser.parse_file(PUZZLES / "thesis7x7.txt")
    result = solve(puzzle, timeout_s=30, ordering="static",
                   propagation="full")
    assert result.solved and is_solved(puzzle, result.bulbs)


def test_determinism():
    puzzle = parser.parse_file(PUZZLES / "thesis7x7.txt")
    for label, solve in VARIANTS:
        a, b = solve(puzzle, timeout_s=30), solve(puzzle, timeout_s=30)
        assert (a.stats.nodes, a.stats.conflicts, a.stats.propagations) == \
               (b.stats.nodes, b.stats.conflicts, b.stats.propagations), label


def test_observer_story_is_consistent():
    puzzle = parser.parse_file(PUZZLES / "thesis7x7.txt")
    events = []
    result = solve_full(puzzle,
                        observer=lambda ev, cell, bulbs: events.append(ev),
                        timeout_s=30)
    assert result.solved
    kinds = set(events)
    assert "place" in kinds and "solution" in kinds
    assert events.count("remove") <= events.count("place")