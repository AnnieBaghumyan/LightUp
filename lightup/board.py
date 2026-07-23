"""Board representation for the LightUp (Akari) puzzle.

THE RULES, EXPLICITLY
---------------------
Given: a grid of cells, each either WHITE or a WALL; some walls carry a
number n in {0,1,2,3,4}.

Define sight(w) for a white cell w: all white cells reachable from w by
walking straight up/down/left/right, stopping at the first wall or the
board edge (w itself not included).  Sight is symmetric.

A SOLUTION is a set B of white cells ("bulbs") such that:

  R1  Illumination:            every white cell w satisfies
                               ({w} | sight(w)) & B != {}    (each bulb
                               lights itself and everything it sees)
  R2  No mutual illumination:  no bulb sees another bulb; equivalently,
                               every maximal wall-free run of white cells
                               in a row/column contains at most one bulb
  R3  Clue exactness:          every numbered wall k has EXACTLY n_k bulbs
                               among its orthogonally adjacent white cells
                               (unnumbered walls constrain nothing)

Solution uniqueness is NOT a rule — published puzzles are merely curated
to be unique.

AS A CSP (AIMA Ch. 6)
---------------------
  variables:    one X_w per white cell w
  domains:      X_w in {bulb, no-bulb}
  constraints:  R1: sum over {w} | sight(w) of X_v  >= 1   per white cell
                R2: sum over segment S of X_v       <= 1   per segment
                R3: sum over N(k) of X_v            == n_k per numbered wall

"Lit" is deliberately NOT a domain value: it is a derived property,
lit(w) <=> ({w} | sight(w)) & B != {}, fully determined by the bulb
assignment and computed on demand by lit_cells().  Adding it as a cell
state would inflate the search space (3^n instead of 2^n) and require
extra constraints just to keep the redundant state consistent.

Design note (this mirrors the problem formulation in our report):

- `Puzzle` holds only the immutable givens: which cells are white, which are
  black walls, and which walls carry a number clue.  It never changes while
  solving.
- A candidate solution is NOT stored inside the Puzzle.  It is simply a set of
  (row, col) tuples marking where bulbs are placed, and it is passed to the
  functions that need it.  In AI terms: Puzzle = the problem definition,
  bulb set = a state / assignment.  Solvers own and mutate their bulb sets.

Coordinates are (row, col), zero-based, row 0 at the top.
"""

EMPTY = "."           # white cell (a bulb may be placed here)
WALL = "#"            # black wall without a number
CLUE_CHARS = "01234"  # black wall with a clue: exactly n adjacent bulbs

# The four orthogonal directions: up, down, left, right.
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


class Puzzle:
    """An immutable LightUp board (walls and clues only, no bulbs)."""

    def __init__(self, rows):
        """rows: list of equal-length strings made of '.', '#' and '0'-'4'.

        Input checking is done by parser.parse(); this class trusts its input.
        """
        self.grid = list(rows)
        self.height = len(self.grid)
        self.width = len(self.grid[0]) if self.grid else 0

    # ----- basic cell queries ------------------------------------------------

    def in_bounds(self, r, c):
        return 0 <= r < self.height and 0 <= c < self.width

    def is_white(self, r, c):
        """True for cells where a bulb could be placed."""
        return self.grid[r][c] == EMPTY

    def is_wall(self, r, c):
        """True for black cells, numbered or not."""
        return self.grid[r][c] != EMPTY

    def clue(self, r, c):
        """The number on a wall (0-4), or None if the cell has no number."""
        ch = self.grid[r][c]
        return int(ch) if ch in CLUE_CHARS else None

    # ----- geometry helpers used by the validator and (later) the solvers ---

    def white_cells(self):
        """All (r, c) positions where a bulb could be placed."""
        return [(r, c)
                for r in range(self.height)
                for c in range(self.width)
                if self.is_white(r, c)]

    def clue_cells(self):
        """All (r, c) positions of numbered walls."""
        return [(r, c)
                for r in range(self.height)
                for c in range(self.width)
                if self.clue(r, c) is not None]

    def neighbors(self, r, c):
        """Orthogonally adjacent in-bounds cells (used for clue checking)."""
        return [(r + dr, c + dc)
                for dr, dc in DIRECTIONS
                if self.in_bounds(r + dr, c + dc)]

    def white_neighbors(self, r, c):
        """Adjacent white cells: the only places a clue's bulbs can go."""
        return [(nr, nc) for nr, nc in self.neighbors(r, c)
                if self.is_white(nr, nc)]

    def cells_seen_from(self, r, c):
        """White cells visible from (r, c) along its row and column.

        "Visible" means walking up/down/left/right until a wall or the edge
        of the board.  This is exactly the set of cells a bulb at (r, c)
        would light up, and equally the set of cells whose bulbs would clash
        with a bulb at (r, c).  The cell (r, c) itself is not included.
        """
        seen = []
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            while self.in_bounds(nr, nc) and not self.is_wall(nr, nc):
                seen.append((nr, nc))
                nr, nc = nr + dr, nc + dc
        return seen


def lit_cells(puzzle, bulbs):
    """The set of all white cells illuminated by the given bulbs.

    A bulb lights its own cell plus everything it can see (cells_seen_from).
    """
    lit = set()
    for r, c in bulbs:
        lit.add((r, c))
        lit.update(puzzle.cells_seen_from(r, c))
    return lit
