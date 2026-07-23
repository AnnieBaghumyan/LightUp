"""Common interface shared by every solver in the project.

All solvers — backtracking and its variants, hill climbing, simulated
annealing — return the same SolveResult, so the CLI, the GUI animation and
the experiment harness can treat them uniformly.

Observability: a solver accepts an optional `observer` callback and calls it
as observer(event, cell, bulbs) on every interesting step:

    "place"     a bulb was placed on `cell`
    "skip"      the solver decided `cell` stays empty
    "remove"    the bulb on `cell` was taken back (backtracking)
    "conflict"  the last decision broke a rule; the branch is abandoned
    "solution"  a complete valid solution was found (cell is None)

`bulbs` is the solver's live working set — read it, never mutate it.  This
one hook powers the CLI's --log and --step modes and, later, the GUI's
step-by-step animation.
"""

from dataclasses import dataclass, field


@dataclass
class Stats:
    """Search-effort counters, the currency of our solver comparison."""
    nodes: int = 0        # decisions tried (bulb or no-bulb)
    conflicts: int = 0    # decisions rejected by the consistency check
    backtracks: int = 0   # bulb placements undone
    time_ms: float = 0.0  # wall-clock solving time


@dataclass
class SolveResult:
    solved: bool
    bulbs: set                     # the solution found (empty if none)
    stats: Stats = field(default_factory=Stats)
    timed_out: bool = False
