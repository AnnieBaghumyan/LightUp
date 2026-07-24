"""Smart backtracking: heuristic ordering + inference (AIMA Chapter 6).

Same problem as backtracking.py (see board.py for rules R1-R3), same
observer events, same SolveResult — but the search maintains explicit
knowledge per cell (bulb / no-bulb / undecided) and uses it, instead of
re-validating the whole board from scratch at every node.

Two configurations, chosen by the `propagation` argument:

  "forward"  Forward checking + pruning.  Placing a bulb immediately marks
             every cell it sees as no-bulb (those cells are lit, so a bulb
             there would clash — rule R2 enforced the moment it becomes
             enforceable).  Before recursing we also prune branches where
             a clue can no longer be met (R3 window check) or an unlit
             cell has no possible lighter left (R1 support check) —
             the same conditions the naive solver rediscovers by full
             rescans, here answered from the maintained state.

  "full"     All of the above plus propagation to a fixpoint:
             - saturated clue  (placed == n): remaining neighbors -> no-bulb
             - exhausted clue  (placed + free == n): free neighbors -> bulb
             - forced lighter  (unlit cell with exactly ONE undecided cell
               able to light it): that cell -> bulb
             Each inferred assignment can trigger more inference; we loop
             until nothing changes.  This is the "trivial solver" of
             Pulles (2021) generalized into in-search inference, and a
             hand-rolled GAC-style propagation on our counting constraints.

Variable ordering (`ordering="smart"`): decide first a free neighbor of
the clue with the tightest slack (free - still_needed); if no clue is
unfinished, the cell that could light the most-constrained unlit cell
(fewest remaining lighters).  This is the degree/most-constrained-variable
idea adapted to LightUp; with binary domains plus propagation, classic MRV
degenerates (forced cells are assigned by inference before search sees
them).  `ordering="static"` falls back to row-major for ablation runs.

Value ordering: bulb first, like the baseline — a bulb makes progress on
R1 and lets forward checking prune, so it fails faster when wrong.
"""

import sys
import time

from ..validator import is_solved
from .base import SolveResult, Stats

BULB, EMPTY = True, False


def solve(puzzle, observer=None, timeout_s=None,
          ordering="smart", propagation="full"):
    """Backtracking search with maintained domains.  Stops at the first
    solution.  See the module docstring for `ordering` / `propagation`."""

    # ----- immutable geometry, computed once (the naive solver recomputes
    # sight lines implicitly on every validator call) ------------------------
    whites = puzzle.white_cells()
    sight = {w: tuple(puzzle.cells_seen_from(*w)) for w in whites}
    clues = [(puzzle.clue(r, c), tuple(puzzle.white_neighbors(r, c)))
             for r, c in puzzle.clue_cells()]

    # ----- search state ------------------------------------------------------
    value = {}                      # cell -> BULB / EMPTY; absent = undecided
    bulbs = set()                   # decided bulbs (mirrors value, for speed)
    lit_count = {w: 0 for w in whites}   # how many bulbs light each cell
    trail = []                      # assignment order, for undo
    stats = Stats()
    notify = observer or (lambda event, cell, bulbs: None)
    start = time.perf_counter()
    timed_out = False
    solution = None

    sys.setrecursionlimit(max(1000, 2 * len(whites) + 100))

    def out_of_time():
        nonlocal timed_out
        if timeout_s is not None and time.perf_counter() - start > timeout_s:
            timed_out = True
        return timed_out

    # ----- assigning and undoing --------------------------------------------
    def assign(cell, val, inferred=False):
        """Record cell = val.  Placing a bulb forward-checks rule R2: every
        cell it sees becomes no-bulb.  Returns False on direct conflict."""
        prev = value.get(cell)
        if prev is not None:
            return prev == val      # re-deriving a known fact is fine
        value[cell] = val
        trail.append(cell)
        if inferred:
            stats.propagations += 1
        if val is BULB:
            bulbs.add(cell)
            lit_count[cell] += 1
            notify("place", cell, bulbs)
            for s in sight[cell]:
                lit_count[s] += 1
            for s in sight[cell]:
                if value.get(s) is BULB:
                    return False    # two bulbs see each other
                if value.get(s) is None and not assign(s, EMPTY, True):
                    return False
        else:
            notify("skip", cell, bulbs)
        return True

    def undo(mark):
        """Roll the trail back to `mark`, reversing bulbs and lighting."""
        while len(trail) > mark:
            cell = trail.pop()
            val = value.pop(cell)
            if val is BULB:
                bulbs.discard(cell)
                lit_count[cell] -= 1
                for s in sight[cell]:
                    lit_count[s] -= 1
                notify("remove", cell, bulbs)

    # ----- pruning and propagation ------------------------------------------
    def feasible():
        """Prune-only lookahead (the "forward" configuration).

        R3 window: a clue is dead if it already has too many bulbs or too
        few cells left that could still take one.  R1 support: an unlit,
        decided-empty cell with no undecided cell in sight can never be lit.
        """
        for n, nbrs in clues:
            placed = free = 0
            for x in nbrs:
                v = value.get(x)
                if v is BULB:
                    placed += 1
                elif v is None:
                    free += 1
            if placed > n or placed + free < n:
                return False
        for w in whites:
            if lit_count[w] or value.get(w) is None:
                continue            # lit, or may still hold a bulb itself
            if not any(value.get(s) is None for s in sight[w]):
                return False
        return True

    def propagate():
        """Inference to a fixpoint (the "full" configuration).  Returns
        False on contradiction.  Every inferred assignment may enable more
        inference, so we loop until a full pass changes nothing."""
        while True:
            changed = False
            for n, nbrs in clues:
                placed = [x for x in nbrs if value.get(x) is BULB]
                free = [x for x in nbrs if value.get(x) is None]
                if len(placed) > n or len(placed) + len(free) < n:
                    return False
                if free and len(placed) == n:          # saturated clue
                    for x in free:
                        if not assign(x, EMPTY, True):
                            return False
                    changed = True
                elif free and len(placed) + len(free) == n:  # exhausted clue
                    for x in free:
                        if value.get(x) is None and not assign(x, BULB, True):
                            return False
                    changed = True
            for w in whites:
                if lit_count[w]:
                    continue
                cands = [x for x in (w, *sight[w]) if value.get(x) is None]
                if not cands:
                    return False    # unlit and nothing can ever light it
                if len(cands) == 1:                    # forced lighter
                    if not assign(cands[0], BULB, True):
                        return False
                    changed = True
            if not changed:
                return True

    # ----- variable ordering -------------------------------------------------
    def pick_static():
        for w in whites:
            if value.get(w) is None:
                return w
        return None

    def pick_smart():
        # 1) a free neighbor of the tightest unfinished clue
        best, best_slack = None, None
        for n, nbrs in clues:
            placed = free = 0
            first_free = None
            for x in nbrs:
                v = value.get(x)
                if v is BULB:
                    placed += 1
                elif v is None:
                    free += 1
                    if first_free is None:
                        first_free = x
            if not free or placed >= n:
                continue            # finished (or saturated) clue
            slack = free - (n - placed)
            if best_slack is None or slack < best_slack:
                best, best_slack = first_free, slack
        if best is not None:
            return best
        # 2) a candidate lighter of the most-constrained unlit cell
        best, best_k = None, None
        for w in whites:
            if lit_count[w]:
                continue
            cands = [x for x in (w, *sight[w]) if value.get(x) is None]
            if cands and (best_k is None or len(cands) < best_k):
                best, best_k = cands[0], len(cands)
        if best is not None:
            return best
        return pick_static()        # only over-satisfied leftovers remain

    pick = pick_smart if ordering == "smart" else pick_static
    consistent = propagate if propagation == "full" else feasible

    # ----- the search ---------------------------------------------------------
    def backtrack():
        nonlocal solution
        if out_of_time() or solution is not None:
            return
        cell = pick()
        if cell is None:
            # Everything decided; the goal test confirms clue EXACTNESS too.
            if is_solved(puzzle, bulbs):
                solution = set(bulbs)
                notify("solution", None, bulbs)
            return
        for val in (BULB, EMPTY):
            mark = len(trail)
            stats.nodes += 1
            ok = assign(cell, val) and consistent()
            if ok:
                backtrack()
            else:
                stats.conflicts += 1
                notify("conflict", cell, bulbs)
            if solution is not None:
                return              # keep the solved state intact
            undo(mark)
            if val is BULB:
                stats.backtracks += 1
            if out_of_time():
                return

    # Root propagation: forced moves that exist before any decision
    # (0-clues, 4-clues, corner 2s...) are inference, not search.
    root_ok = consistent()
    if root_ok:
        backtrack()
    stats.time_ms = (time.perf_counter() - start) * 1000

    return SolveResult(solved=solution is not None,
                       bulbs=solution or set(),
                       stats=stats,
                       timed_out=timed_out)


def solve_forward(puzzle, observer=None, timeout_s=None):
    """Convenience wrapper: forward checking + pruning, smart ordering."""
    return solve(puzzle, observer, timeout_s, propagation="forward")


def solve_full(puzzle, observer=None, timeout_s=None):
    """Convenience wrapper: full inference, smart ordering."""
    return solve(puzzle, observer, timeout_s, propagation="full")
