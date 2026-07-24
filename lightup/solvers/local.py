"""Local search solvers: hill climbing and simulated annealing (AIMA Ch. 4).

A completely different formulation from the backtracking family:

    state      a COMPLETE assignment — simply a set of bulb positions
    objective  cost(B) = (# unlit white cells)
                       + (# pairs of bulbs that see each other)
                       + Σ over numbered walls |placed_k − n_k|
               Each term counts violations of one rule (R1, R2, R3), so
               cost(B) = 0  ⟺  B is a solution.
    moves      add a bulb, remove a bulb, or relocate one (remove + add) —
               the 3-action neighborhood that Perera et al. (2021) found
               to outperform 2 actions.
    start      a random full lighting built like the generator does
               (Pulles 2021, Algorithm 1): repeatedly light a random
               still-unlit cell.  By construction R1 and R2 already hold,
               so the initial cost is just the clue deviation.

Both solvers are INCOMPLETE: they can fail on solvable puzzles (and can
never prove unsolvability), which is exactly the property our experiments
measure against the complete backtracking family.

Hill climbing: sample `neighbors_per_step` random neighbors, jump to the
best one if it strictly improves the cost; otherwise the state is a local
optimum and we RESTART from a fresh random lighting.

Simulated annealing: propose ONE random neighbor at a time; always accept
improvements, accept a worsening of Δ with probability exp(−Δ/T); the
temperature T cools geometrically.  When T reaches t_min without a
solution, we reheat (restart with a fresh state and T = t0).

Stats mapping (documented because the fields were named for tree search):
    nodes        candidate states evaluated (HC) / proposals made (SA)
    conflicts    steps stuck in a local optimum (HC) / rejected proposals (SA)
    backtracks   restarts (HC) / reheats (SA)
    propagations unused (0) — there is no inference here

Randomness is controlled by `seed` so experiments are reproducible.  The
observer receives "place"/"remove" diffs of ACCEPTED moves only (plus the
initial lighting), so the GUI replay shows the state evolving.
"""

import random
import time

from ..validator import is_solved
from .base import SolveResult, Stats


def make_cost(puzzle):
    """Precompute geometry and return (whites, sight, cost_function)."""
    whites = puzzle.white_cells()
    sight = {w: tuple(puzzle.cells_seen_from(*w)) for w in whites}
    clues = [(puzzle.clue(r, c), tuple(puzzle.white_neighbors(r, c)))
             for r, c in puzzle.clue_cells()]

    def cost(bulbs):
        lit = set(bulbs)
        for b in bulbs:
            lit.update(sight[b])
        unlit = len(whites) - len(lit)
        pairs = sum(1 for b in bulbs for s in sight[b] if s in bulbs) // 2
        deviation = sum(abs(sum(1 for x in nbrs if x in bulbs) - n)
                        for n, nbrs in clues)
        return unlit + pairs + deviation

    return whites, sight, cost


def _random_full_lighting(whites, sight, rng):
    """Pulles Algorithm 1: light random unlit cells until everything is lit.
    Guarantees no two bulbs see each other (an unlit cell is, by
    definition, out of every existing bulb's sight)."""
    bulbs, unlit = set(), set(whites)
    while unlit:
        b = rng.choice(sorted(unlit))   # sorted -> reproducible with a seed
        bulbs.add(b)
        unlit.discard(b)
        unlit.difference_update(sight[b])
    return bulbs


def _random_neighbor(bulbs, whites, rng):
    """One random move: add / remove / relocate a bulb."""
    empties = [w for w in whites if w not in bulbs]
    actions = []
    if empties:
        actions.append("add")
    if bulbs:
        actions.append("remove")
    if bulbs and empties:
        actions.append("move")
    action = rng.choice(actions)
    neighbor = set(bulbs)
    if action in ("remove", "move"):
        neighbor.remove(rng.choice(sorted(bulbs)))
    if action in ("add", "move"):
        neighbor.add(rng.choice(empties))
    return neighbor


def _emit_diff(notify, old, new):
    """Tell the observer how the accepted state differs from the previous."""
    for cell in sorted(old - new):
        notify("remove", cell, new)
    for cell in sorted(new - old):
        notify("place", cell, new)


def solve_hillclimb(puzzle, observer=None, timeout_s=10, seed=None,
                    neighbors_per_step=30):
    """Hill climbing with random restarts.  Runs until solved or timeout."""
    whites, sight, cost = make_cost(puzzle)
    rng = random.Random(seed)
    stats = Stats()
    notify = observer or (lambda event, cell, bulbs: None)
    start = time.perf_counter()

    current = _random_full_lighting(whites, sight, rng)
    _emit_diff(notify, set(), current)
    current_cost = cost(current)
    best_cost = current_cost

    while current_cost > 0:
        if time.perf_counter() - start > timeout_s:
            stats.time_ms = (time.perf_counter() - start) * 1000
            return SolveResult(False, set(), stats, timed_out=True,
                               best_cost=best_cost)

        # Evaluate a sample of neighbors, keep the best one.
        best_neighbor, best_neighbor_cost = None, None
        for _ in range(neighbors_per_step):
            candidate = _random_neighbor(current, whites, rng)
            stats.nodes += 1
            c = cost(candidate)
            if best_neighbor_cost is None or c < best_neighbor_cost:
                best_neighbor, best_neighbor_cost = candidate, c

        if best_neighbor_cost < current_cost:      # strict improvement
            _emit_diff(notify, current, best_neighbor)
            current, current_cost = best_neighbor, best_neighbor_cost
            best_cost = min(best_cost, current_cost)
        else:                                      # local optimum: restart
            stats.conflicts += 1
            stats.backtracks += 1
            fresh = _random_full_lighting(whites, sight, rng)
            _emit_diff(notify, current, fresh)
            current, current_cost = fresh, cost(fresh)
            best_cost = min(best_cost, current_cost)

    stats.time_ms = (time.perf_counter() - start) * 1000
    assert is_solved(puzzle, current)   # cost == 0 must mean solved
    notify("solution", None, current)
    return SolveResult(True, set(current), stats, best_cost=0)


def solve_annealing(puzzle, observer=None, timeout_s=10, seed=None,
                    t0=2.5, cooling=0.9995, t_min=0.01):
    """Simulated annealing with reheating.  Runs until solved or timeout."""
    import math

    whites, sight, cost = make_cost(puzzle)
    rng = random.Random(seed)
    stats = Stats()
    notify = observer or (lambda event, cell, bulbs: None)
    start = time.perf_counter()

    current = _random_full_lighting(whites, sight, rng)
    _emit_diff(notify, set(), current)
    current_cost = cost(current)
    best_cost = current_cost
    temperature = t0

    while current_cost > 0:
        if time.perf_counter() - start > timeout_s:
            stats.time_ms = (time.perf_counter() - start) * 1000
            return SolveResult(False, set(), stats, timed_out=True,
                               best_cost=best_cost)

        candidate = _random_neighbor(current, whites, rng)
        stats.nodes += 1
        delta = cost(candidate) - current_cost
        if delta < 0 or rng.random() < math.exp(-delta / temperature):
            _emit_diff(notify, current, candidate)
            current, current_cost = candidate, current_cost + delta
            best_cost = min(best_cost, current_cost)
        else:
            stats.conflicts += 1

        temperature *= cooling
        if temperature < t_min:                    # cooled out: reheat
            stats.backtracks += 1
            fresh = _random_full_lighting(whites, sight, rng)
            _emit_diff(notify, current, fresh)
            current, current_cost = fresh, cost(fresh)
            best_cost = min(best_cost, current_cost)
            temperature = t0

    stats.time_ms = (time.perf_counter() - start) * 1000
    assert is_solved(puzzle, current)   # cost == 0 must mean solved
    notify("solution", None, current)
    return SolveResult(True, set(current), stats, best_cost=0)
