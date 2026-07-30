"""All solving algorithms, one module per approach.

- base.py          shared SolveResult / Stats and the observer contract
- backtracking.py  naive backtracking (the baseline)
- csp.py           smart backtracking: forward checking / full inference
- local.py         local search: hill climbing / simulated annealing

SOLVERS is the single registry the GUI (and any other front-end) uses:
display name -> solve(puzzle, observer=None, timeout_s=None) callable.
"""

from .backtracking import solve as solve_naive
from .base import SolveResult, Stats
from .csp import solve_forward, solve_full
from .local import solve_annealing, solve_hillclimb

SOLVERS = {
    "backtracking (naive)": solve_naive,
    "BT + forward checking": solve_forward,
    "BT + full inference": solve_full,
    "hill climbing": solve_hillclimb,
    "simulated annealing": solve_annealing,
}

# The two families report different things.  Backtracking hits conflicts and
# backtracks; local search accepts moves and measures a cost, and never emits
# a "conflict" event at all.  Front-ends use this to label progress honestly
# instead of showing a conflict counter that can only ever read zero.
LOCAL_SEARCH = frozenset({"hill climbing", "simulated annealing"})
