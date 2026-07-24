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
9. **Findings (all measured, all reproducible):**
   * Full inference: 75/75 instances, the only 100 % solver; the
     published 7×7 solved with 0 search nodes / 41 propagations — pure
     deduction, consistent with human-solvable curation.
   * Naive→fc→full: 1–2 orders of magnitude fewer nodes; naive solves
     0 % at 25×25.
   * Fewer nodes ≠ less time: full needs ~2× fewer nodes than fc but fc
     is slightly faster per board at large sizes (propagation overhead).
   * SA ≫ HC: 45/75 vs 21/75 overall (19/25 vs 11/25 hard) —
     independent reproduction of Perera et al. HC's signature failure:
     stuck at cost 1 (one run: 12,496 restarts in 20 s, never closed).
   * Density surprise: sparse "hard" preset often FASTER for solvers
     (fewer clues → more solutions → easier to find one); HC inverts
     (solved only some hard, nothing easy/medium at 14×14 — dense clue
     terms create local optima). Presets model human difficulty, not
     search difficulty.
   * Budget robustness: doubling 5 s→10 s changed ≤3/75 per solver;
     HC exactly 0. Predictions pre-registered; the SA prediction (big
     gains) was wrong — honest to report. One-liner: more time helps
     slow solvers, not stuck ones; the ranking is structural.
10. **Experimental design points:** identical instances for all solvers;
    deterministic regeneration — the dataset IS (size, difficulty, seed)
    triples, reconstructible anywhere, no puzzle files needed; local
    solvers seeded with the instance seed, so the 10 s runs replay the
    5 s trajectories exactly (paired comparison); caveat to state: 5
    instances per bucket is modest — per-bucket rates move in 20-point
    steps; aggregate claims (75 runs/solver) are robust. Rerun with
    --seeds 20 if time allows and refresh numbers.

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
