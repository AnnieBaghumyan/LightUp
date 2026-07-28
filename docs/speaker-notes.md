# Speaker script

> The full text to say, slide by slide (~9-10 minutes total), plus
> stage cues. Rehearse from this, then deliver it in your own
> phrasing — reading aloud verbatim always sounds worse than it reads.

## Speaker assignment (balanced by speaking time)

| Speaker | Slides | ~time |
|---|---|---|
| Izabella Atajanyan | 1–4 (title, rules, why, formulation) | ~3.3 min |
| Ani Baghumyan | 5–8 (solvers, system, setup, inference results) | ~4.0 min |
| Anna Gasparyan | 9–13 (local search, difficulty, robustness, conclusions, Q&A lead) | ~3.6 min |

Swap freely — just keep the three shares roughly equal (equal input is
graded) and hand over cleanly between slides 4→5 and 8→9.

## Slide 1 — Title  (~30 s)

**Say:** Good morning. Our project is LightUp — also known as Akari — a Japanese logic puzzle. We built the game itself, and then made five different AI solvers compete on it. The board you see here is a published puzzle, solved by our own system. Let me start with the rules.

*Stage cue: One presenter opens; keep it moving.*

## Slide 2 — The puzzle: three rules  (~1 min)

**Say:** LightUp has three rules. You place light bulbs on white cells. Rule one: every white cell must be lit — a bulb lights its whole row and column until a wall blocks the light. Rule two: no bulb may shine on another bulb. Rule three: a numbered wall must have exactly that many bulbs next to it — exactly, not at most. In this small example the corner two forces both of its neighbors, and one more bulb finishes the board. One detail worth remembering: nothing in the rules says a puzzle has only one solution — uniqueness is a publishing convention, and that detail will come back in our results.

*Stage cue: Point at the 3x3 while explaining. Do not dwell.*

## Slide 3 — Why LightUp is a good AI problem  (~1 min)

**Say:** Why is this a good AI problem? Three reasons. First, it is NP-complete: it was proven in 2005 to be as hard as circuit satisfiability. Second, it is a very clean constraint-satisfaction problem: one binary variable per white cell. Third, it scales: our generator produces boards from three-by-three up to twenty-five-by-twenty-five with tunable difficulty, which gives us unlimited test data. Earlier work solved LightUp three ways: by translating it into SAT, by modelling it as a constraint problem, and with local search. Our two solver families follow the last two — and later we check whether the published local-search finding still holds on our own instances.

*Stage cue: Prior work stays at one sentence — the course asks for brevity here.*

## Slide 4 — Problem formulation (CSP)  (~45 s)

**Say:** Our formulation: one binary variable per white cell — bulb or no bulb. The three rules become three families of counting constraints: every cell's line of sight must contain at least one bulb; every wall-free segment, at most one; every numbered wall, exactly its number. One design decision worth mentioning: 'lit' is not a variable. Whether a cell is lit follows entirely from where the bulbs are, so storing it as a state would only inflate the search space.

*Stage cue: Do not explain what a CSP is — covered in the course.*

## Slide 5 — One problem, five solvers  (~1 min)

**Say:** We implemented five solvers in two families. On the left, complete search. Plain backtracking is the baseline — it re-checks the whole board at every step. Forward checking adds memory: placing a bulb immediately rules out every cell it sees. Full inference adds deduction, applied over and over: a satisfied clue blocks its remaining neighbors, a clue that needs all its remaining cells forces them, and a cell with only one possible light source left forces that source. Those are exactly the moves a human player makes. On the right, local search: hill climbing and simulated annealing start from a complete random placement and repair it, guided by a score that counts rule violations — zero violations means solved. Every solver reports the same statistics, so the comparison is fair.

*Stage cue: This slide is the experiment design in one picture.*

## Slide 6 — The system  (~45 s)

**Say:** Everything is observable. This is our game — you can play it yourself, including the X marks human players use for notes. The same window animates any solver: in this screenshot the naive solver is mid-search on a ten-by-ten — the red frame is a conflict it just hit, and the status bar shows it has already tried eighty-eight thousand nodes. This replay tool is how we debugged the solvers, and honestly, how we came to understand them.

*Stage cue: If Q&A time allows, a 20-second live solve beats this slide — have the game open in a background window. Never show code.*

## Slide 7 — Experimental setup  (~45 s)

**Say:** The experiment: five board sizes from seven to twenty-five, three difficulty presets from clue-dense to sparse, five seeded instances per combination — seventy-five unique puzzles — and every solver gets identical puzzles with a five-second budget: three hundred seventy-five runs. Everything is seeded, so every number that follows is reproducible. And one principle: we judge correctness by the rules themselves, never by comparing to a stored answer, because a board can have several legal solutions.

## Slide 8 — Results — what does inference buy?  (~1.5 min)

**Say:** So, what does inference buy? Two headline numbers. On the published seven-by-seven, the naive solver needs three hundred and eight search nodes. Forward checking needs twelve. Full inference needs zero — the puzzle is solved entirely by deduction, no search at all. And that makes sense: publishers design puzzles that humans can deduce. Across the whole sweep, full inference solved all seventy-five instances — the only solver with a perfect record. The charts show the scaling: the naive curve leaves the picture after eighteen-by-eighteen — it solves nothing at twenty-five — while both smart variants stay one to two orders of magnitude lower. One honest nuance: full inference uses about half the nodes of forward checking, yet forward checking is slightly faster per board at the largest sizes, because propagation costs time at every node. Fewer nodes is not automatically less time.

*Stage cue: THE core slide. Say 308 -> 12 -> 0 slowly.*

## Slide 9 — Results — complete vs. local search  (~1.5 min)

**Say:** Now the other paradigm. This chart shows the solve rate within five seconds on hard instances. Simulated annealing clearly beats hill climbing everywhere — nineteen out of twenty-five versus eleven — which independently reproduces the published result of Perera and colleagues. Why does hill climbing fail? It gets stuck. In one twenty-second run it restarted twelve and a half thousand times and ended every attempt exactly one violation away from the goal. That is a local optimum in its purest form — and annealing's willingness to temporarily accept worse states is precisely what escapes it. Overall, though, within this budget, complete search with inference dominated local search at every size we tested. And one structural caveat: local search can never prove a board unsolvable.

*Stage cue: The one-violation-away story is the local-optimum concept made concrete — deliver it as a story.*

## Slide 10 — Results — what makes an instance hard?  (~1 min)

**Say:** What makes an instance hard? Here we got a genuine surprise. Our hard preset — few walls, few clues — is hard for humans, but often faster for solvers: fewer clues means more valid solutions, and finding any one of them is easier. Hill climbing shows the mirror image: at fourteen-by-fourteen it solved nothing at easy or medium density, but sometimes cracked the sparse boards — dense clues create exactly the local optima that trap it. So our difficulty presets model human difficulty, not search difficulty — and calibrating them by measured effort is future work.

## Slide 11 — Robustness — is the 5 s budget arbitrary?  (~20 s)

**Say:** One robustness check: we re-ran the entire sweep with double the budget — almost nothing changed, and hill climbing gained exactly zero — so the ranking you have seen is structural, not an artifact of the timeout.

*Stage cue: One sentence, then move on. Q&A backup: predictions were made before the run; the one miss was SA (expected bigger gains) — exponential problems shrug at factors of two.*

## Slide 12 — Conclusions  (~45 s)

**Say:** To conclude. Inference was the story: full propagation solved everything we generated, and cracked the reference puzzle without any search. Fewer nodes is not the same as less time. Simulated annealing beats hill climbing, confirming prior work — and hill climbing's failures are structural, stuck one step from the goal. Sparse boards turned out easier for solvers than for humans. Future work: generating unique-solution puzzles, arc consistency, and difficulty calibration. Thank you — we are happy to take questions.

*Stage cue: All three members should have spoken by now.*

## Slide 13 — References  (not spoken)

*Stage cue: Present for completeness and Q&A only.*
