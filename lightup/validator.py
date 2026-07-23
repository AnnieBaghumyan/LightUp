"""Checking bulb placements against the LightUp rules.

The rules R1 (all lit), R2 (no bulb sees a bulb), R3 (clues exact) are
stated formally at the top of board.py.  Violation kinds map onto them:

    R2 broken now:        bulbs_see_each_other
    R3 broken now:        clue_exceeded            (already > n)
    R3 unreachable:       clue_unsatisfiable       (can never reach n)
    R1 failed (final):    cell_unlit
    R3 failed (final):    clue_unmet               (< n in a full solution)
    placement error:      bulb_not_on_white

Every check returns a list of Violation records instead of a bare boolean.
This is deliberate: the CLI and (later) the solvers' logs can then explain
*why* a placement is wrong, which makes the search behavior inspectable
instead of a black box.

Two levels of checking:

- check_partial():  rules that must hold for ANY placement, even unfinished.
  Backtracking search (Chapter 6, CSPs) will call this to prune branches.
- check_solution(): partial rules + completeness (all cells lit, clues met
  exactly).  This is the goal test of the search problem.
"""

from dataclasses import dataclass

from .board import lit_cells


@dataclass(frozen=True)
class Violation:
    kind: str      # short machine-readable tag, e.g. "clue_exceeded"
    cells: tuple   # the cells involved, e.g. the two clashing bulbs
    message: str   # human-readable explanation

    def __str__(self):
        return self.message


def check_partial(puzzle, bulbs):
    """Consistency of a (possibly unfinished) placement.  Empty list = OK.

    Detects:
    - bulb_not_on_white:    a bulb on a wall or outside the board
    - bulbs_see_each_other: two bulbs share a row/column with no wall between
    - clue_exceeded:        a numbered wall already has too many bulbs
    - clue_unsatisfiable:   a numbered wall can no longer reach its number,
                            because too few of its neighbor cells can still
                            take a bulb (a neighbor is unavailable once it is
                            lit by some other bulb)
    """
    bulbs = set(bulbs)
    violations = []

    # Rule 0: bulbs may only sit on white cells.
    for r, c in sorted(bulbs):
        if not puzzle.in_bounds(r, c) or not puzzle.is_white(r, c):
            violations.append(Violation(
                "bulb_not_on_white", ((r, c),),
                f"bulb at ({r},{c}) is not on a white cell"))
    # Ignore the illegal ones for the remaining checks.
    bulbs = {(r, c) for r, c in bulbs
             if puzzle.in_bounds(r, c) and puzzle.is_white(r, c)}

    # Rule 1: no two bulbs may light each other.
    for r, c in sorted(bulbs):
        for other in puzzle.cells_seen_from(r, c):
            if other in bulbs and (r, c) < other:  # report each pair once
                violations.append(Violation(
                    "bulbs_see_each_other", ((r, c), other),
                    f"bulbs at ({r},{c}) and ({other[0]},{other[1]}) "
                    "light each other"))

    lit = lit_cells(puzzle, bulbs)

    # Rule 2: numbered walls.
    for r, c in puzzle.clue_cells():
        n = puzzle.clue(r, c)
        adjacent = puzzle.white_neighbors(r, c)
        placed = sum(1 for cell in adjacent if cell in bulbs)

        if placed > n:
            violations.append(Violation(
                "clue_exceeded", ((r, c),),
                f"clue {n} at ({r},{c}) already has {placed} adjacent "
                "bulb(s)"))

        # A neighbor can still take a bulb only if it has no bulb and is not
        # lit by another bulb (a lit cell would clash with the bulb lighting
        # it).  If even using every such free cell cannot reach n, this
        # placement can never be completed into a solution.
        free = sum(1 for cell in adjacent
                   if cell not in bulbs and cell not in lit)
        if placed + free < n:
            violations.append(Violation(
                "clue_unsatisfiable", ((r, c),),
                f"clue {n} at ({r},{c}) has {placed} bulb(s) and only "
                f"{free} free neighbor cell(s) left"))

    return violations


def check_solution(puzzle, bulbs):
    """Full goal test.  Empty list = the puzzle is solved.

    Adds on top of check_partial():
    - cell_unlit:  a white cell that no bulb illuminates
    - clue_unmet:  a numbered wall with fewer bulbs than its number
    """
    bulbs = set(bulbs)
    violations = check_partial(puzzle, bulbs)
    lit = lit_cells(puzzle, bulbs)

    for r, c in puzzle.white_cells():
        if (r, c) not in lit:
            violations.append(Violation(
                "cell_unlit", ((r, c),),
                f"white cell ({r},{c}) is not lit"))

    for r, c in puzzle.clue_cells():
        n = puzzle.clue(r, c)
        placed = sum(1 for cell in puzzle.white_neighbors(r, c)
                     if cell in bulbs)
        if placed < n:
            violations.append(Violation(
                "clue_unmet", ((r, c),),
                f"clue {n} at ({r},{c}) has only {placed} adjacent bulb(s)"))

    return violations


def is_solved(puzzle, bulbs):
    """Convenience goal-test wrapper: True iff no violations at all."""
    return not check_solution(puzzle, bulbs)


def involved_cells(violations, kinds=None):
    """All cells mentioned by the given violations, as a set.

    kinds: optional set of violation kinds to include (None = all).  The GUI
    uses this to highlight offending cells without knowing any game rules.
    """
    cells = set()
    for v in violations:
        if kinds is None or v.kind in kinds:
            cells.update(v.cells)
    return cells
