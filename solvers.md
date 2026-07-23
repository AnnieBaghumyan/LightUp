# Solvers

This document explains each solving approach in the project: how it works,
what it deliberately does or does not do, and how to observe and measure it.
It grows as solvers are added.

The problem the solvers share is stated formally at the top of
[`lightup/board.py`](lightup/board.py): rules R1 (every white cell lit),
R2 (no bulb sees another bulb), R3 (numbered walls have exactly their number
of adjacent bulbs), and the CSP view — one variable X_w ∈ {bulb, no-bulb}
per white cell, with R1–R3 as constraints over sums of these variables.
Correctness of any solver is always judged by the validator
([`lightup/validator.py`](lightup/validator.py)), never by comparing against
one known answer, because a puzzle may legitimately have several solutions.

---

## 1. Naive backtracking (`lightup/backtracking.py`)

The baseline. Every later solver exists to beat it, and its statistics are
the yardstick.

### Formulation

| CSP element | Choice |
|---|---|
| Variables | white cells, in **fixed row-major order** (reading order) |
| Domain | {bulb, no-bulb}, tried in that order (bulb first) |
| Constraints | R1–R3, checked through `validator.check_partial` |
| Goal test | `validator.is_solved` (all cells lit, clues met exactly) |

### The algorithm

Depth-first search over the decision sequence:

1. Take the next undecided cell in row-major order.
2. **Option 1:** place a bulb there. Run the consistency check. If it
   passes, recurse into the next cell; if it fails, count a conflict and
   abandon the branch. Either way, remove the bulb afterwards (backtrack).
3. **Option 2:** leave the cell empty. Same consistency check, same
   recursion.
4. When all cells are decided, run the full goal test. The search stops at
   the first solution found. An optional timeout bounds the search on hard
   instances.

Because each of the n white cells has two options, the search tree has up
to 2^n leaves — LightUp is NP-complete (McPhail 2005), so some exponential
worst case is expected; the entire project is about how much of that tree
clever solvers can avoid visiting.

### What "consistent" means here

Two kinds of checking happen at every node (see `consistent()` in the
code):

1. **Assignment consistency** — do the already-decided variables violate a
   constraint among themselves? Detects: two bulbs seeing each other
   (R2 broken), a clue with more adjacent bulbs than its number
   (R3 exceeded).
2. **Satisfiability lookahead** — can each constraint still be completed?
   Detects: a clue that can no longer reach its number because too few of
   its neighbor cells can still take a bulb (`clue_unsatisfiable`), and the
   **doomed-cell rule**: an unlit cell whose own cell and entire line of
   sight are already decided bulb-free can never be lit, so the branch is
   hopeless. This is the lookahead form of R1; without it the search would
   still be *complete* (bad leaves fail the goal test) but would wade
   through enormous obviously-dead subtrees on even tiny boards.

In CSP vocabulary: the baseline checks assignment consistency plus
constraint-wipeout detection. It maintains **no domains** and does **no
propagation** — it is not node/arc consistency, and every node pays a full
re-scan of the board to rediscover facts a propagating solver would cache.

### What is deliberately naive

* No variable-ordering heuristic — cells come in reading order, however
  unpromising (compare: MRV / degree heuristics).
* No value-ordering heuristic (compare: least-constraining value).
* No inference — nothing is propagated from clues (compare: forward
  checking, clue propagation, AC-3).
* The consistency check re-validates the whole board from scratch at every
  node, O(cells × sight) per node, instead of updating incrementally.

Each bullet is a planned experiment: the smarter variants change exactly
one of these choices and the statistics show what it buys.

### Statistics and observability

Every solver returns a `SolveResult` with a `Stats` record:

* `nodes` — decisions tried (bulb or no-bulb),
* `conflicts` — decisions rejected by the consistency check,
* `backtracks` — bulb placements undone,
* `time_ms` — wall-clock time,

plus `timed_out`. An optional observer callback receives every event
(`place`, `skip`, `remove`, `conflict`, `solution`), which powers the CLI's
`--log`/`--step` modes and the GUI's animated replay (Solve / Play/Pause /
Step / Finish in the game window).

Reference point (thesis 7×7 puzzle from Pulles 2021, Fig. 2.1): solved in
308 nodes, 149 conflicts, 159 backtracks, ~15 ms. Finding the solution is
much cheaper than proving it unique: exhausting the same puzzle's full
search tree to rule out a second solution took ~1 800 nodes.

### How to run it

```
python -m lightup solve puzzles/thesis7x7.txt            # solve + stats
python -m lightup solve puzzles/corner2.txt --log        # decision log
python -m lightup solve puzzles/corner2.txt --step       # interactive
python -m lightup play puzzles/thesis7x7.txt             # GUI animation
```

---

## Planned

* **Backtracking + heuristics** — MRV/degree variable ordering, value
  ordering. Same search, better decisions first.
* **Backtracking + inference** — forward checking with explicit per-cell
  domains, clue propagation (0/4-clues and saturated/exhausted clues force
  their neighbors), optionally AC-3 on the binary no-mutual-illumination
  constraints. Same conditions as the baseline's lookahead, computed
  incrementally instead of by full re-scan.
* **Hill climbing** and **simulated annealing** — local search over
  complete assignments with a violation-counting objective; a different
  paradigm entirely, incomplete but often fast.
