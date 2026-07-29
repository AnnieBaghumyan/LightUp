# Speaker script

> The full text to say, slide by slide (~9-10 minutes total), plus
> stage cues. Rehearse from this, then deliver it in your own
> phrasing — reading aloud verbatim always sounds worse than it reads.
>
> Generated from presentation.pptx by sync_speaker_notes.py — edit the
> notes in the deck, then re-run, so the two never disagree.

## Speaker assignment (balanced by speaking time)

| Speaker | Slides | ~time |
|---|---|---|
| Izabella Atajanyan | 1–4 (title, rules, why, formulation) | ~3.3 min |
| Ani Baghumyan | 5–8 (solvers, system, setup, inference results) | ~4.0 min |
| Anna Gasparyan | 9–13 (local search, difficulty, robustness, conclusions, Q&A lead) | ~3.6 min |

Swap freely — just keep the three shares roughly equal (equal input is
graded) and hand over cleanly between slides 4→5 and 8→9.

## Slide 1 — Light Up Akari with AI Search  (~30 s)

**Say:** Good morning. Our project is LightUp — also known as Akari — a Japanese logic puzzle. We built the game itself, and then made five different AI solvers compete on it. The board you see here is a published puzzle, solved by our own system. Let me start with the rules.

> Cue: One presenter opens; keep it moving.

## Slide 2 — The puzzle: three rules  (~1 min)

**Say:** LightUp has three rules. You place light bulbs on white cells. Rule one: every white cell must be lit — a bulb lights its whole row and column until a wall blocks the light. Rule two: no bulb may shine on another bulb. Rule three: a numbered wall must have exactly that many bulbs next to it — exactly, not at most. In this small example the corner two forces both of its neighbors, and one more bulb finishes the board.

One detail worth remembering: nothing in the rules says a puzzle has only one solution — uniqueness is a publishing convention, and that detail will come back in our results.

> Cue: Point at the 3x3 while explaining. Do not dwell.

## Slide 3 — Why LightUp is a good AI problem  (~1 min)

**Say:** Why is this a good AI problem? Three reasons. First, it is NP-complete: it was proven in 2005 to be as hard as circuit satisfiability. Second, it is a very clean constraint-satisfaction problem: one binary variable per white cell. Third, it scales: our generator produces boards from three-by-three up to twenty-five-by-twenty-five with tunable difficulty, which gives us unlimited test data. Earlier work solved LightUp three ways: by translating it into SAT, by modelling it as a constraint problem, and with local search. Our two solver families follow the last two — and later we check whether the published local-search finding still holds on our own instances.

> Cue: Prior work stays at one sentence — the course asks for brevity here.

> Q&A trap: if NP-complete, why did you solve 25x25 in 20 ms? Because NP-completeness is a WORST-CASE statement. Puzzle-like instances carry a lot of structure, and inference exploits it; the hard instances the theory guarantees exist are not the ones a puzzle generator usually produces.

## Slide 4 — Problem formulation (CSP)  (~45 s)

**Say:** Our formulation: one binary variable per white cell — bulb or no bulb. The three rules become three families of constraints: every cell's line of sight must contain at least one bulb; every wall-free segment, at most one; every numbered wall, exactly its number. Whether a cell is lit follows entirely from where the bulbs are.

> Cue: Do not explain what a CSP is — covered in the course.

## Slide 5 — One problem, five solvers  (~1 min)

**Say:** We implemented five solvers in two families. 
On the left, backtracking search - it builds a partial assignment, one cell at a time, and backtracks it when stuck. All three are complete. They differ only in how much inference they do.
Plain backtracking does none. Forward checking deletes values: place a bulb, and every cell it sees loses the option of being a bulb. Full inference keeps applying the constraints until nothing changes - a clue that already has all its bulbs empties the rest, a clue that needs every cell it has left fills them, a cell with one possible light source forces that source. These are the moves a human player makes.
On the right, local search. Both start from a random fully lit board and repair it, guided by a score that counts broken rules - zero means solved. Both are incomplete. The difference is which moves they accept. Hill climbing takes only improvements, so it stalls at a local optimum and restarts. Simulated annealing sometimes accepts a worse board, less and less over time.

> Cue: This slide is the experiment design in one picture.

## Slide 6 — The system: game, generator, observable solvers  (~45 s)

**Say:** Everything is observable. This is our game - you can play it yourself. The window animates all solvers: in this screenshot the naive solver is mid-search on a ten-by-ten - the red frame is a conflict it just hit, and the status bar shows it has already tried eighty-eight thousand nodes. This replay tool is how we debugged the solvers, and honestly, how we came to understand them.

> Cue: If Q&A time allows, a 20-second live solve beats this slide — have the game open in a background window. Never show code.

## Slide 7 — Experimental setup  (~45 s)

**Say:** The experiment: five board sizes from seven to twenty-five, three difficulty presets from clue-dense to sparse, five seeded instances per combination - seventy-five unique puzzles - and every solver gets identical puzzles with a five-second budget: three hundred seventy-five runs. And one principle: we judge correctness by the rules themselves, never by comparing to a stored answer, because a board can have several legal solutions.

## Slide 8 — Results — what does inference buy?  (~1 min)

**Say:** What does inference buy? On the published seven-by-seven, full inference places every bulb by deduction - no search at all, where the naive solver needs hundreds of guesses. Publishers design puzzles humans can reason through, and our rules are those same steps.
Full inference solved everything we generated - the only solver with a perfect record.
The chart shows the baseline giving up: naive leaves the picture after eighteen-by-eighteen, while both informed variants stay far lower - about ten times fewer nodes at seven-by-seven, and about fifty times fewer by eighteen.
One nuance. Full inference always expands fewer nodes, but propagation is not free - it re-checks every clue at every node, even when nothing new comes out. On clue-rich boards that pays back. On the sparse boards plotted here it does not, and forward checking wins.

> Cue: THE core slide. Say ZERO slowly and let it land. Q&A backup - the exact numbers on that puzzle are 308 naive, 12 forward checking, 0 full; the chart is a median over five GENERATED hard boards, where naive is 94.

## Slide 9 — Results — complete vs. local search  (~1.5 min)

**Say:** Now the other paradigm. This chart shows the solve rate within five seconds on hard instances. Simulated annealing clearly beats hill climbing everywhere — nineteen out of twenty-five versus eleven — which independently reproduces the published result of Perera and colleagues. Why does hill climbing fail? It gets stuck. In one twenty-second run it restarted twelve and a half thousand times and ended every attempt exactly one violation away from the goal. That is a local optimum in its purest form — and annealing's willingness to temporarily accept worse states is precisely what escapes it. Overall, though, within this budget, complete search with inference dominated local search at every size we tested. And one structural caveat: local search can never prove a board unsolvable.

> Cue: The one-violation-away story is the local-optimum concept made concrete — deliver it as a story.

## Slide 10 — Results — what makes an instance hard?  (~1 min)

**Say:** What makes an instance hard? Here we got a genuine surprise. Our hard preset — few walls, few clues — is hard for humans, but often faster for solvers: fewer clues means more valid solutions, and finding any one of them is easier. Hill climbing shows the mirror image: at fourteen-by-fourteen it solved nothing at easy or medium density, but sometimes cracked the sparse boards — dense clues create exactly the local optima that trap it. So our difficulty presets model human difficulty, not search difficulty.

## Slide 11 — Robustness — is the 5 s budget arbitrary?  (~20 s)

**Say:** One robustness check: we re-ran the entire sweep with double the budget — almost nothing changed, and hill climbing gained exactly zero — so the ranking you have seen is structural, not an artifact of the timeout.

> Cue: One sentence, then move on. Q&A backup: predictions were made before the run; the one miss was SA (expected bigger gains) — exponential problems shrug at factors of two.

## Slide 12 — Conclusions  (~45 s)

**Say:** To conclude. Inference was the story: full propagation solved everything we generated, and cracked the reference puzzle without any search. Fewer nodes is not the same as less time. Simulated annealing beats hill climbing, confirming prior work — and hill climbing's failures are structural, stuck one step from the goal. Sparse boards turned out easier for solvers than for humans. Future work: generating puzzles with a guaranteed unique solution, writing our own SAT solver so we can compare a clause-based formulation against our constraint-based one, and calibrating difficulty from measured search effort rather than from clue density. Thank you — we are happy to take questions.

> Cue: All three members should have spoken by now.

## Slide 13 — References  (not spoken)

*(nothing spoken)*

> Cue: Present for completeness and Q&A only.
