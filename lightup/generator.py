"""Random LightUp puzzle generator.

Puzzles are built "solution-first", so every generated puzzle is guaranteed
to be solvable by construction — no solver needed:

1. Place walls on the grid (optionally with 180-degree rotational symmetry,
   the style used by published Akari puzzles).
2. Build a valid bulb placement: repeatedly put a bulb on a random cell that
   is still unlit.  An unlit cell is, by definition, not in the line of
   sight of any existing bulb, so this can never create a conflict.  This is
   Algorithm 1 in Pulles (2021): Akari without numbers is solvable in
   polynomial time.
3. Copy clue numbers onto a fraction of the walls (the number of bulbs the
   built solution has around them), then take the bulbs away.

The result has at least one solution: the one we just built.  Whether it is
the ONLY solution is not checked here — that requires a solver and is
revisited in a later step, exactly as in Pulles (2021).

Every function takes an explicit seed so that experiments are reproducible:
the same seed always yields the same puzzle.
"""

import random

from .board import Puzzle, EMPTY, WALL

# Board sizes we support (both width and height).
MIN_SIZE, MAX_SIZE = 3, 25

# Difficulty presets = constraint density.  Easy boards are packed with
# walls and every wall has a number, so most bulb positions are forced;
# hard boards are open and sparsely numbered, leaving much more choice.
# NOTE for the report: until the solvers exist this is a *proxy* for
# difficulty; once backtracking lands we can measure real search effort per
# preset and calibrate these numbers with data.
DIFFICULTY = {
    "easy":   {"wall_density": 0.25, "clue_density": 1.00},
    "medium": {"wall_density": 0.18, "clue_density": 0.80},
    "hard":   {"wall_density": 0.12, "clue_density": 0.55},
}


def generate(height, width, *, wall_density=0.18, clue_density=0.85,
             symmetric=True, seed=None):
    """Create one random solvable puzzle.

    wall_density: fraction of all cells that become walls (roughly).
    clue_density: fraction of walls that receive a clue number.
    symmetric:    mirror every wall through the board center (aesthetics
                  only; has no effect on solvability).
    Returns (puzzle, solution_bulbs) — the solution is the bulb set the
    puzzle was built from, handy for tests and demos.
    """
    rng = random.Random(seed)

    # --- step 1: walls ------------------------------------------------------
    walls = set()
    target = round(height * width * wall_density)
    cells = [(r, c) for r in range(height) for c in range(width)]
    rng.shuffle(cells)
    for r, c in cells:
        if len(walls) >= target:
            break
        walls.add((r, c))
        if symmetric:
            walls.add((height - 1 - r, width - 1 - c))

    puzzle_without_clues = Puzzle([
        "".join(WALL if (r, c) in walls else EMPTY for c in range(width))
        for r in range(height)])

    # --- step 2: a valid bulb placement (Pulles 2021, Algorithm 1) ----------
    bulbs = set()
    unlit = set(puzzle_without_clues.white_cells())
    while unlit:
        bulb = rng.choice(sorted(unlit))  # sorted -> same seed, same puzzle
        bulbs.add(bulb)
        unlit.discard(bulb)
        unlit.difference_update(puzzle_without_clues.cells_seen_from(*bulb))

    # --- step 3: clues from the solution, then remove the bulbs -------------
    grid = [[WALL if (r, c) in walls else EMPTY for c in range(width)]
            for r in range(height)]
    for r, c in sorted(walls):
        if rng.random() < clue_density:
            adjacent = sum(1 for cell in puzzle_without_clues.neighbors(r, c)
                           if cell in bulbs)
            grid[r][c] = str(adjacent)

    puzzle = Puzzle(["".join(row) for row in grid])
    return puzzle, bulbs
