"""Naive backtracking solver — the project's baseline.

CSP formulation (AIMA Chapter 6):
    variables:   the white cells, visited in fixed row-major order
    domains:     {bulb, no-bulb}, tried in that order
    constraints: the LightUp rules, checked by validator.check_partial

The search is depth-first: decide the next cell (bulb first, then no-bulb),
check consistency, recurse, undo.  It is DELIBERATELY naive:

  * no variable-ordering heuristic — cells come in reading order, however
    unpromising;
  * no value-ordering heuristic;
  * no inference — nothing is propagated from clues;
  * the consistency check re-validates the whole board from scratch at
    every single node.

The smarter variants built later (heuristic ordering, forward checking,
clue propagation) exist precisely to beat this solver, and Stats is how we
measure by how much.

One pruning rule beyond check_partial is required for the search to be
*correct* rather than clever: a "doomed cell" check.  Once every cell that
could possibly light some cell w has been decided as no-bulb, w can never
be lit and the branch is hopeless.  Without this rule the search would
still be complete (leaves get a full goal test) but would wade through
enormous obviously-dead subtrees on even tiny boards.
"""

import sys
import time

from .board import lit_cells
from .solver import SolveResult, Stats
from .validator import check_partial, is_solved


def solve(puzzle, observer=None, max_solutions=1, timeout_s=None):
    """Depth-first search for up to `max_solutions` solutions.

    max_solutions=2 turns this into a uniqueness checker: if only one
    solution comes back after an exhaustive search, the puzzle is unique.
    """
    order = puzzle.white_cells()           # fixed row-major variable order
    index = {cell: i for i, cell in enumerate(order)}
    bulbs = set()
    stats = Stats()
    solutions = []
    notify = observer or (lambda event, cell, bulbs: None)
    start = time.perf_counter()
    timed_out = False

    # The recursion goes one level per white cell (625 on a 25x25 board).
    sys.setrecursionlimit(max(1000, 2 * len(order) + 100))

    def out_of_time():
        nonlocal timed_out
        if timeout_s is not None and time.perf_counter() - start > timeout_s:
            timed_out = True
        return timed_out

    def consistent(depth):
        """May the current partial assignment still lead to a solution?

        Naive on purpose: the whole board is re-checked every time.  A cell
        is "decided" when its position in the fixed order is < depth.
        """
        if check_partial(puzzle, bulbs):
            return False
        # Doomed-cell rule: an unlit cell whose own cell AND every cell in
        # its line of sight are already decided (hence bulb-free) can never
        # be lit anymore.
        lit = lit_cells(puzzle, bulbs)
        for w in order:
            if w in lit or index[w] >= depth:
                continue  # already lit, or w itself may still get a bulb
            if all(index[seen] < depth
                   for seen in puzzle.cells_seen_from(*w)):
                return False
        return True

    def backtrack(depth):
        if depth == len(order):
            # Every cell decided and every partial check passed on the way
            # down; the full goal test also verifies clues are met EXACTLY.
            if is_solved(puzzle, bulbs):
                solutions.append(set(bulbs))
                notify("solution", None, bulbs)
            return
        if out_of_time() or len(solutions) >= max_solutions:
            return
        cell = order[depth]

        # Option 1: place a bulb on this cell.
        stats.nodes += 1
        bulbs.add(cell)
        notify("place", cell, bulbs)
        if consistent(depth + 1):
            backtrack(depth + 1)
        else:
            stats.conflicts += 1
            notify("conflict", cell, bulbs)
        bulbs.remove(cell)
        stats.backtracks += 1
        notify("remove", cell, bulbs)

        if out_of_time() or len(solutions) >= max_solutions:
            return

        # Option 2: leave this cell empty.
        stats.nodes += 1
        notify("skip", cell, bulbs)
        if consistent(depth + 1):
            backtrack(depth + 1)
        else:
            stats.conflicts += 1
            notify("conflict", cell, bulbs)

    backtrack(0)
    stats.time_ms = (time.perf_counter() - start) * 1000

    return SolveResult(solved=bool(solutions),
                       bulbs=set(solutions[0]) if solutions else set(),
                       solutions=solutions,
                       stats=stats,
                       timed_out=timed_out)
