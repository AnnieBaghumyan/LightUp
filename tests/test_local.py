"""Tests for the local search solvers (hill climbing, simulated annealing).

Local search is randomized and incomplete, so these tests always fix seeds
and use generous-but-small time budgets.  Correctness of any solution is
judged by the validator, as everywhere else.
"""

from pathlib import Path

from lightup import parser
from lightup.generator import DIFFICULTY, generate
from lightup.solvers.local import make_cost, solve_annealing, solve_hillclimb
from lightup.validator import is_solved

PUZZLES = Path(__file__).resolve().parent.parent / "puzzles"
THESIS_SOLUTION = {(0, 0), (1, 3), (2, 4), (3, 5),
                   (4, 2), (4, 6), (5, 1), (5, 5), (6, 0), (6, 6)}
SOLVERS = [("hill climbing", solve_hillclimb),
           ("simulated annealing", solve_annealing)]


# ----- the objective function ------------------------------------------------

def test_cost_is_zero_exactly_on_solutions():
    puzzle = parser.parse_file(PUZZLES / "thesis7x7.txt")
    _, _, cost = make_cost(puzzle)
    assert cost(THESIS_SOLUTION) == 0
    assert cost(set()) > 0                          # nothing lit
    assert cost(THESIS_SOLUTION - {(6, 6)}) > 0     # unlit cells + clue short
    assert cost(THESIS_SOLUTION | {(3, 3)}) > 0     # seeing pair appears


# ----- solving ---------------------------------------------------------------

def test_local_solvers_solve_small_fixtures():
    for name in ["tiny3x3.txt", "corner2.txt"]:
        puzzle = parser.parse_file(PUZZLES / name)
        for label, solve in SOLVERS:
            result = solve(puzzle, seed=0, timeout_s=10)
            assert result.solved, (name, label)
            assert is_solved(puzzle, result.bulbs), (name, label)
            assert result.best_cost == 0


def test_local_solvers_solve_the_thesis_puzzle():
    puzzle = parser.parse_file(PUZZLES / "thesis7x7.txt")
    for label, solve in SOLVERS:
        result = solve(puzzle, seed=1, timeout_s=20)
        assert result.solved, label
        assert is_solved(puzzle, result.bulbs), label


def test_local_solvers_solve_generated_boards():
    for seed in range(3):
        puzzle, _ = generate(7, 7, seed=seed, **DIFFICULTY["medium"])
        for label, solve in SOLVERS:
            result = solve(puzzle, seed=seed, timeout_s=20)
            assert result.solved, (seed, label)
            assert is_solved(puzzle, result.bulbs), (seed, label)


def test_unsolvable_board_times_out_gracefully():
    puzzle = parser.parse_file(PUZZLES / "unsolvable3x3.txt")
    for label, solve in SOLVERS:
        result = solve(puzzle, seed=0, timeout_s=1)
        assert not result.solved and result.timed_out, label
        assert result.best_cost is not None and result.best_cost > 0, label


def test_same_seed_same_run():
    puzzle = parser.parse_file(PUZZLES / "corner2.txt")
    for label, solve in SOLVERS:
        a = solve(puzzle, seed=7, timeout_s=10)
        b = solve(puzzle, seed=7, timeout_s=10)
        assert (a.solved, a.stats.nodes, a.stats.conflicts) == \
               (b.solved, b.stats.nodes, b.stats.conflicts), label


def test_observer_sees_state_diffs():
    puzzle = parser.parse_file(PUZZLES / "corner2.txt")
    events = []
    result = solve_annealing(
        puzzle, observer=lambda ev, cell, bulbs: events.append((ev, cell)),
        seed=0, timeout_s=10)
    assert result.solved
    # Replaying place/remove events must reconstruct the returned solution.
    state = set()
    for ev, cell in events:
        if ev == "place":
            state.add(cell)
        elif ev == "remove":
            state.discard(cell)
    assert state == result.bulbs