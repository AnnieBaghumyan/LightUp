"""Tests for the random puzzle generator.

The key property is the whole point of solution-first construction: every
generated puzzle must be solvable by the very bulb set it was built from.
"""

from lightup.board import WALL
from lightup.generator import generate
from lightup.validator import is_solved


def test_generated_puzzles_are_solvable():
    # Many seeds and sizes; the built-from solution must always be valid.
    for seed in range(20):
        for height, width in [(5, 5), (7, 7), (10, 6)]:
            puzzle, solution = generate(height, width, seed=seed)
            assert puzzle.height == height and puzzle.width == width
            assert is_solved(puzzle, solution), \
                f"seed {seed}, size {height}x{width} produced a bad puzzle"


def test_same_seed_same_puzzle():
    a, sol_a = generate(7, 7, seed=42)
    b, sol_b = generate(7, 7, seed=42)
    assert a.grid == b.grid and sol_a == sol_b


def test_different_seeds_differ():
    a, _ = generate(7, 7, seed=1)
    b, _ = generate(7, 7, seed=2)
    assert a.grid != b.grid


def test_symmetry_flag():
    puzzle, _ = generate(9, 9, seed=3, symmetric=True)
    h, w = puzzle.height, puzzle.width
    walls = {(r, c) for r in range(h) for c in range(w)
             if puzzle.is_wall(r, c)}
    mirrored = {(h - 1 - r, w - 1 - c) for r, c in walls}
    assert walls == mirrored


def test_density_knobs():
    # clue_density=0 -> walls but no numbers; wall_density=0 -> open board.
    puzzle, _ = generate(7, 7, clue_density=0.0, seed=4)
    assert all(puzzle.clue(r, c) is None
               for r in range(7) for c in range(7))
    open_board, solution = generate(7, 7, wall_density=0.0, seed=5)
    assert all(open_board.is_white(r, c) for r in range(7) for c in range(7))
    assert is_solved(open_board, solution)
