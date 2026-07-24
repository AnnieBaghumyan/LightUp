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

## 1. Naive backtracking (`lightup/solvers/backtracking.py`)

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
* `propagations` — assignments made by inference, not by search,
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

## 2. Smart backtracking (`lightup/solvers/csp.py`)

Same search skeleton, but the solver *maintains knowledge* per cell
(bulb / no-bulb / undecided, plus a lit-counter) instead of re-validating
the board from scratch at every node. Two configurations:

### `fc` — forward checking + pruning

* Placing a bulb immediately marks every cell it sees as no-bulb
  (rule R2 enforced the moment it becomes enforceable).
* Before recursing: prune if any clue can no longer be met (R3 window) or
  any unlit cell has no possible lighter left (R1 support) — the same
  conditions the baseline rediscovers by full rescans, answered here from
  the maintained state.

### `full` — forward checking + propagation to a fixpoint

Adds inference rules that *assign* rather than merely prune, looping until
nothing changes:

* **saturated clue** (placed = n): remaining neighbors → no-bulb;
* **exhausted clue** (placed + free = n): free neighbors → bulb;
* **forced lighter**: an unlit cell with exactly one undecided cell able
  to light it forces that bulb.

This is Pulles (2021)'s "trivial solver" generalized into in-search
inference — a hand-rolled GAC-style propagation on the counting
constraints. Root-level propagation runs before any search, so forced
moves (0/4-clues, corner 2s…) are inference, not decisions.

### Variable ordering

`smart` (default): decide first a free neighbor of the tightest unfinished
clue (slack = free − still-needed); otherwise a candidate lighter of the
most-constrained unlit cell. Classic MRV degenerates here: domains are
binary and propagation auto-assigns forced cells before search sees them,
so the degree/most-constrained idea does the work. `static` (row-major) is
available for ablation runs.

### Measured (same machine, single runs)

| puzzle | solver | nodes | conflicts | propagations | time |
|---|---|---|---|---|---|
| thesis 7×7 | naive | 308 | 149 | 0 | 15 ms |
| thesis 7×7 | fc | 12 | 1 | 31 | 0.2 ms |
| thesis 7×7 | full | **0** | 0 | 41 | 0.3 ms |
| 14×14 hard | naive | 333 | 153 | 0 | 64 ms |
| 14×14 hard | fc | 146 | 61 | 375 | 8 ms |
| 14×14 hard | full | 23 | 0 | 149 | 5 ms |

The zero is the headline: the published 7×7 is solved **entirely by
propagation, with no search at all** — consistent with how publishers
curate puzzles to be human-deducible. The systematic experiments (many
seeds, growing sizes) belong to the experiment harness step.

```
python -m lightup solve puzzles/thesis7x7.txt --solver bt|fc|full
```

The backtracking family is now **feature-frozen**: one baseline and these
two configurations. Further variants (AC-3/MAC, LCV, …) are future work,
not project scope.

---

## Planned

* **Hill climbing** and **simulated annealing** — local search over
  complete assignments with a violation-counting objective; a different
  paradigm entirely, incomplete but often fast.
* **Experiment harness** — instance sweeps (size × difficulty × seeds),
  aggregated stats, matplotlib figures for the report and slides.
