# Report working notes

> **These are raw working notes for writing the report — NOT report text.**
> The course strictly requires the report to be written by the team, in
> your own words, in narrative (not bullet) form. Use these notes to
> remember arguments and numbers; never copy sentences from here.

## Where things live

| You need | Look in |
|---|---|
| Formal rules R1–R3, CSP formulation, "lit is derived" argument | `lightup/board.py` top docstring |
| Each solver: algorithm, design choices, measured numbers | `solvers.md` §1–3 |
| Experiment protocol, findings, budget experiment | `solvers.md` §4 |
| Raw data | `experiments/results/results.csv` (5 s), `results_10s.csv` |
| Figures | `experiments/results/fig1..fig4*.png` (regenerate: `plot.py`) |
| Decision history | `git log` — commit messages explain every step |

## Suggested mapping to the required report structure

* **Introduction** — LightUp rules informally; why it is a good AI testbed
  (NP-complete, clean CSP, scalable generated instances); goal: implement
  several course techniques and compare them experimentally.
* **Literature review** — McPhail 2005 (NP-completeness via Circuit-SAT);
  Pulles 2021 (backtracking + "trivial solver" + SAT via Z3; our full
  inference generalizes his trivial solver; our uniqueness discussion
  follows his generator); Perera/Sun/Browning 2021 (HC/SA fitness and the
  3-action neighborhood; their SA≫HC result, which we reproduce);
  Salcedo-Sanz 2009 (evolutionary, mention only). AIMA Ch. 3/4/6 for the
  algorithm families.
* **Method** — formulation (from board.py), the five solvers (from
  solvers.md), generator (solution-first construction), experimental
  design (below). Detailed enough to recreate = list exact parameters.
* **Evaluation** — the four figures with the findings listed below.
* **Conclusions** — the five conclusion bullets of the presentation,
  expanded; future work: uniqueness-filtered generation, AC-3/MAC,
  difficulty calibration by measured effort, own-DPLL SAT route.

## Arguments discussed that the report should make (in your words)

1. **"Lit" is not a variable.** Lighting is a derived property of the
   bulb assignment — adding it as a cell state would inflate the space
   3^n vs 2^n and need extra consistency constraints. (Perera et al. DO
   use a lit cell state — but that is a *display/NN input* encoding, not
   a search formulation. Distinguishing representation-for-algorithm
   from representation-for-display is worth a paragraph.)
2. **Uniqueness is a publishing convention, not a rule.** The rules
   define a CSP that may have many solutions; published puzzles are
   curated to have exactly one (Pulles' generator loops until unique).
   Consequence: solver correctness must be judged by the rules validator,
   never by comparison to one known answer. Our generator guarantees
   solvability by construction (build solution → derive clues → remove
   bulbs) but not uniqueness — uniqueness checking needs a solution
   counter, listed as future work.
3. **Constraint taxonomy.** R2 in pairwise form is binary (at-most-one
   per segment decomposes losslessly into pairs); R1 and R3 are global
   (counting) constraints; R3's exactly-k does NOT decompose into binary
   without auxiliary variables. No unary constraints in the base model —
   they appear as derived special cases (0-clue ⇒ neighbors no-bulb).
4. **What the naive solver's `consistent()` is, precisely:** assignment
   consistency (violations among decided variables) + constraint-wipeout
   lookahead (clue window, doomed cell). It is NOT arc consistency: no
   domains are maintained, nothing is propagated or cached. Don't
   overclaim in the report — examiners pounce.
5. **Why the doomed-cell rule lives in the solver, not the validator:**
   the validator's world is (puzzle, bulbs) and cannot distinguish "no
   bulb yet" from "committed no-bulb" — that distinction is search
   state (`index[cell] < depth`). `clue_unsatisfiable` CAN live in the
   validator because "cell cannot take a bulb" is derivable from bulbs
   alone (a lit cell would clash). Also: the GUI calls check_partial on
   hand-play states, where doomed-flagging would be false alarms.
6. **fc vs full = detect vs infer.** Forward checking prunes (detects
   wipeout); full inference additionally ASSIGNS (saturated clue,
   exhausted clue, forced lighter) and loops to a fixpoint — a hand-
   rolled GAC-style propagation on counting constraints, and Pulles'
   trivial solver generalized into in-search inference.
7. **Relation to logic (Ch. 7) without implementing SAT:** cell variable
   ↔ proposition; R1's "some lighter exists" ↔ a clause; the forced-
   lighter rule ↔ unit propagation; backtracking ↔ DPLL splitting. So
   `full` is structurally DPLL on counting constraints instead of
   clauses. We deliberately did not implement a SAT route: the course
   bans solver libraries (Z3, as Pulles used, would not qualify as own
   implementation), an own DPLL + exactly-k CNF encoding costs 1–2 days,
   and the marginal insight is captured by this paragraph. Cite Pulles'
   SAT results as the clause-based counterpart.
8. **Local search formulation:** state = complete bulb set; cost =
   unlit + seeing-pairs + Σ|placed−n| with the property cost = 0 ⟺
   solved (one term per rule — objective and goal test provably agree);
   moves add/remove/relocate (Perera's better 3-action set); initial
   state via Pulles' Algorithm 1 (random full lighting: R1+R2 hold by
   construction, initial cost = clue deviation only). Both HC and SA are
   incomplete — can never prove unsolvability.
9. **Findings** — see the dedicated section "Detailed results" below.
10. **Experimental design points:** identical instances for all solvers;
    deterministic regeneration — the dataset IS (size, difficulty, seed)
    triples, reconstructible anywhere, no puzzle files needed; local
    solvers seeded with the instance seed, so the 10 s runs replay the
    5 s trajectories exactly (paired comparison); caveat to state: 5
    instances per bucket is modest — per-bucket rates move in 20-point
    steps; aggregate claims (75 runs/solver) are robust. Rerun with
    --seeds 20 if time allows and refresh numbers.

## Detailed results

All numbers below come from `experiments/results/results.csv` (5 s
budget) and `results_10s.csv` (10 s). Design: 5 sizes × 3 difficulties ×
5 seeded instances = 75 puzzles; every solver gets the identical puzzles;
375 runs per sweep. "Median" always means median over *solved* runs.

### R1. Solve rate by solver and board size (15 runs per cell)

| solver | 7×7 | 10×10 | 14×14 | 18×18 | 25×25 | total |
|---|---|---|---|---|---|---|
| naive BT | 15/15 | 14/15 | 11/15 | 5/15 | 0/15 | 45/75 |
| forward checking | 15/15 | 15/15 | 15/15 | 14/15 | 9/15 | 68/75 |
| **full inference** | 15/15 | 15/15 | 15/15 | 15/15 | **15/15** | **75/75** |
| hill climbing | 14/15 | 5/15 | 2/15 | 0/15 | 0/15 | 21/75 |
| simulated annealing | 15/15 | 15/15 | 11/15 | 4/15 | 0/15 | 45/75 |

Reading: full inference is the only solver that never failed. Naive BT
collapses at 18×18 and solves nothing at 25×25. Local search degrades
earliest — HC is already mostly failing at 10×10.

### R2. Search effort — median nodes (all difficulties)

| solver | 7×7 | 10×10 | 14×14 | 18×18 | 25×25 |
|---|---|---|---|---|---|
| naive BT | 94 | 407 | 2 281 | 1 741 | — |
| forward checking | 14 | 25 | 54 | 146 | 235 |
| full inference | 5 | 10 | 14 | 25 | 41 |
| hill climbing | 6 675 | 16 440 | 75 120 | — | — |
| simulated annealing | 3 434 | 14 974 | 27 996 | 29 199 | — |

Two comments. (a) The gap between naive and the informed variants grows
with size: ×7 at 7×7, ×40 at 10×10, ×160 at 14×14 — i.e. inference does
not merely add a constant saving, it changes the growth rate. (b) The
naive column *drops* from 14×14 to 18×18 (2 281 → 1 741) — survivorship
bias, not improvement: at 18×18 only the 5 easiest instances were solved
at all, and only those enter the median. Say this explicitly in the
report; it is exactly the kind of artifact an examiner probes.

### R3. Median time, ms (all difficulties)

| solver | 7×7 | 10×10 | 14×14 | 18×18 | 25×25 |
|---|---|---|---|---|---|
| naive BT | 4.1 | 74.1 | 478.6 | 735.0 | — |
| forward checking | 0.3 | 0.8 | 2.8 | 10.7 | 35.8 |
| full inference | 0.3 | 0.8 | 2.5 | 6.8 | 20.6 |
| hill climbing | 79 | 354 | 2 821 | — | — |
| simulated annealing | 44 | 273 | 999 | 1 526 | — |

### R4. When does propagation pay for itself? (fc vs full, median ms)

This is the most interesting comparison in the sweep, and it is
**difficulty-dependent, not size-dependent**:

| difficulty | 7×7 | 10×10 | 14×14 | 18×18 | 25×25 | winner |
|---|---|---|---|---|---|---|
| easy (fc) | 0.40 | 0.69 | 2.80 | 9.42 | 275.42 | |
| easy (full) | 0.31 | 0.61 | 1.11 | 3.88 | **7.73** | full, by 35× at 25×25 |
| medium (fc) | 0.35 | 1.06 | 6.07 | 150.54 | 18.11 | |
| medium (full) | 0.35 | 0.79 | 2.53 | 6.77 | 20.57 | full (tie at 25×25) |
| hard (fc) | **0.27** | **0.77** | **2.01** | **7.05** | **18.87** | fc everywhere |
| hard (full) | 0.35 | 1.13 | 3.63 | 10.91 | 43.78 | |

Mechanism (check it against R5): propagation is an investment paid at
every node. On clue-dense boards there is a great deal to deduce, so the
investment returns many free assignments and full inference wins
outright — at 25×25 easy it is *35× faster* than forward checking. On
sparse boards there is little to deduce, the propagation loop finds
nothing most of the time, and its overhead makes full inference ~2×
slower per board even though it still expands ~half the nodes.

**Correction to make in the report and slides:** it is NOT true that
"full inference is slower at large sizes." It is slower *on sparse
(hard-preset) instances at all sizes*, and much faster on clue-dense
ones. Figure 1 plots hard instances only, which is why it shows the
fc-wins side of this story.

### R5. How much is deduced rather than searched? (full inference)

Median propagations / median nodes, and how many instances were solved
with **no search at all**:

| size | easy | medium | hard | zero-search solves |
|---|---|---|---|---|
| 7×7 | 36 props / 1 node | 34 / 5 | 35 / 8 | 3/15 |
| 10×10 | 74 / 2 | 84 / 10 | 74 / 14 | 2/15 |
| 14×14 | 140 / 6 | 149 / 14 | 151 / 21 | 1/15 |
| 18×18 | 250 / 8 | 282 / 26 | 259 / 32 | 0/15 |
| 25×25 | 477 / 21 | 513 / 41 | 490 / 59 | 0/15 |

Propagation does 10–90× more assignments than search does, and the
search share grows with sparsity (1 node on 7×7 easy vs 8 on 7×7 hard).

Worth a paragraph: the **published** 7×7 from Pulles (2021) is solved
with **0 nodes and 41 propagations** — pure deduction — while only 3 of
our 15 generated 7×7 boards manage that. Plausible explanation to offer
(and label as a hypothesis, not a proven claim): published puzzles are
curated to have a unique solution and to be solvable by human deduction;
our generator guarantees solvability but not uniqueness, so its boards
are less constrained and less deducible. This connects the uniqueness
discussion to a measured effect and motivates uniqueness-filtered
generation as future work.

### R6. Local search: how it fails

| solver | failures | best cost reached (median) | min | distribution highlights |
|---|---|---|---|---|
| hill climbing | 54/75 | 13 | 1 | 5 runs ended at cost 1; long tail to 83 |
| simulated annealing | 30/75 | 5.5 | 1 | 2 runs at cost 1; tail only to 22 |

`best_cost` is the number of remaining rule violations in the best state
found (0 = solved), which is a quality measure tree search does not
have. SA does not merely solve more instances — when it fails it fails
*closer*: median 5.5 vs 13 remaining violations, and its worst case (22)
is far better than HC's (83). Five HC runs ending at exactly one
violation is the local-optimum phenomenon in its purest form; the
separately recorded 20 s run on the hard 14×14 restarted **12 496
times** and never closed that last violation.

### R7. The density inversion (the most surprising result)

Solve rate by difficulty, 25 runs per cell:

| solver | easy | medium | hard |
|---|---|---|---|
| naive BT | 15/25 | 14/25 | 16/25 |
| forward checking | 25/25 | 21/25 | 22/25 |
| full inference | 25/25 | 25/25 | 25/25 |
| hill climbing | 5/25 | 5/25 | **11/25** |
| simulated annealing | 13/25 | 13/25 | **19/25** |

Per size it is even starker — hill climbing at 10×10: easy **0/5**,
medium **0/5**, hard **5/5**; simulated annealing at 18×18: easy 0/5,
medium 0/5, hard 4/5. Naive BT shows a weaker version of the same
inversion at 18×18 (easy 1/5, hard 3/5).

Note the raw search space moves the *opposite* way — at 14×14 the hard
preset leaves ~172 white cells vs ~146 for easy (medians), with ~13
numbered walls vs ~50. So sparse boards have *more* variables and are
still easier for these solvers.

The explanation to develop in the report: **a clue is information for a
solver that can reason with it, and an obstacle for a solver that can
only test it.** Full inference and forward checking exploit clues
directly (hence best on easy). Hill climbing and simulated annealing
cannot reason at all — for them each clue is just another penalty term
in the objective, and clue-dense boards have a rugged landscape full of
local optima. Consequence for the project: our difficulty presets
predict *human* difficulty (length of deduction chains), not search
difficulty; calibrating them against measured effort is future work.

### R8. Budget robustness (5 s vs 10 s, identical instances)

| solver | 5 s | 10 s | Δ | instances gained |
|---|---|---|---|---|
| naive BT | 45/75 | 48/75 | +3 | 14 medium s1, 18 easy s1, 25 easy s3 |
| forward checking | 68/75 | 70/75 | +2 | 18 hard s3, 25 medium s3 |
| full inference | 75/75 | 75/75 | 0 | — (already perfect) |
| hill climbing | 21/75 | 21/75 | **0** | none |
| simulated annealing | 45/75 | 47/75 | +2 | 14 medium s2, 18 hard s0 |

No instance was *lost*, which also confirms the runs are deterministic /
properly seeded. Predictions were written down before this sweep: full
unchanged ✓, bt/fc small gains ✓, HC exactly zero ✓, SA large gains ✗
(we expected more than +2). Reporting the failed prediction honestly is
worth more than hiding it: exponential search shrugs at a factor of two.
Conclusion: **extra time helps solvers that are slow, not solvers that
are stuck** — the ranking is structural, not an artifact of the 5 s
choice.

### Caveats to state explicitly in the report

* 5 instances per (size, difficulty) bucket is modest: a single instance
  moves a per-cell rate by 20 points. Aggregate claims (75 runs per
  solver) are solid; per-cell percentages are indicative. Re-running
  with `--seeds 20` would tighten this if time allows.
* Medians are over solved runs only, so unsolved instances silently drop
  out — this is what produces the naive-BT node dip in R2. Solve rate
  and effort must therefore be read together, never separately.
* Times are wall-clock on one machine in CPython; treat relative
  comparisons as meaningful and absolute milliseconds as indicative.
* Generated instances are solvable by construction but not necessarily
  unique-solution; multi-solution boards are systematically easier for a
  solver that stops at the first solution.

## Reference list (with the role each plays)

* B. McPhail (2005), *Light Up is NP-complete* — complexity grounding.
* B. Pulles (2021), *Analysis of Akari*, Radboud University — trivial
  solver (→ our inference), SAT encoding (the road not taken), generator
  and uniqueness post-processing, the 7×7 reference instance + solution.
* L. Sun, J. Browning, R. Perera (2021), arXiv:2107.10429 — HC/SA
  formulation, 3-action neighborhood, SA ≫ HC (we reproduce).
* S. Salcedo-Sanz et al. (2009), ICGA Journal 32 — evolutionary
  approach, mention in lit review.
* Russell & Norvig, AIMA 4th ed. — Ch. 3 (search), 4 (local search),
  6 (CSPs); cite for the standard algorithms, do not re-explain them.
* puzzle-light-up.com — rules and published-puzzle conventions.

## Figure captions (draft the real ones yourselves)

* Fig 1: search nodes and time vs board size, BT variants, hard
  instances, medians over solved runs, log scale.
* Fig 2: solve rate within 5 s vs size, all five solvers, hard.
* Fig 3: median solve time by difficulty preset at 14×14 (missing bar =
  nothing solved).
* Fig 4: solve rate under 5 s vs 10 s budgets, identical instances.
