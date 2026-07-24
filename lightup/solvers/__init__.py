"""All solving algorithms, one module per approach.

- base.py          shared SolveResult / Stats and the observer contract
- backtracking.py  naive backtracking (the baseline)
- csp.py           smart backtracking: forward checking / full inference

Hill climbing and simulated annealing join this package in a later step.

SOLVERS is the single registry the GUI (and any other front-end) uses:
display name -> solve(puzzle, observer=None, timeout_s=None) callable.
"""

from .backtracking import solve as solve_naive
from .base import SolveResult, Stats
from .csp import solve_forward, solve_full

SOLVERS = {
    "backtracking (naive)": solve_naive,
    "BT + forward checking": solve_forward,
    "BT + full inference": solve_full,
}
