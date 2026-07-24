# Speaker notes / talk track

> Extracted from presentation.pptx. Reword in your own voice while rehearsing.

## Slide 1 - Lighting Up Akari with 

~30s. One presenter opens. Replace member placeholders with real names. The board on the right is the Pulles (2021) example puzzle with its unique solution, drawn by our own renderer's conventions.

## Slide 2 - The puzzle: three rules

~1 min. State the rules quickly with the example. Do NOT dwell — the course requires only a brief problem statement. Mention the uniqueness note; it returns in the analysis.

## Slide 3 - Why LightUp is a good AI problem

~1 min. The three cards are the topic-choice justification. Keep the prior-work strip to two sentences — the course explicitly says existing approaches should be mentioned only very briefly.

## Slide 4 - Problem formulation (CSP)

~45s. One slide of formalism, no more. Do NOT explain what a CSP or backtracking is — covered in the course. The 'lit is derived' line preempts a common Q&A question about the domain.

## Slide 5 - One problem, five solvers

~1 min. The experiment design in one picture: each arrow on the left changes exactly one thing, so differences in the stats are attributable. Right column is the cross-paradigm comparison.

## Slide 6 - The system: game, generator, observable solvers

~45s. The screenshot is the naive solver mid-replay on a 10x10: red frame = conflict at (9,7), green digits = satisfied clues, status bar streams the event counter and search stats. Demo bait: if time allows in Q&A, a 20-second live solve in the GUI is worth more than this slide. Do not show code.

## Slide 7 - Experimental setup

~45s. Fill the two [CONFIRM] blanks once the experiment harness is final. The bottom principle matters in Q&A: multi-solution instances make answer-comparison invalid as a correctness test.

## Slide 8 - Results — what does inference buy?

~1.5 min. THE core slide. Say the numbers out loud: naive 308 nodes on the 7x7, forward checking 12, full inference ZERO - the published puzzle is solved by deduction alone, which is exactly what publishers curate for. Then the scaling panels: 1-2 orders of magnitude between naive and the smart variants. Close with the nodes-vs-time nuance - fewer nodes is not automatically less time.

## Slide 9 - Results — complete vs. local search

~1.5 min. Cross-paradigm comparison. Lead with SA vs HC (the Perera reproduction), then the one-violation-away story - it is the local-optimum concept made concrete. End on the honest framing: on these sizes complete search wins; incompleteness is the structural caveat.

## Slide 10 - Results — what makes an instance hard?

~1 min. The beyond-the-obvious slide. The headline: our density presets predict difficulty for HUMANS (deduction chains), not for solvers - sparse boards have many solutions and finding any one is easy. Tie back to the uniqueness discussion. Calibrating difficulty by measured effort is named future work.

## Slide 11 - Robustness — is the 5 s budget arbitrary?

ONE sentence, ~20s: 'We re-ran the entire sweep with double the budget - almost nothing changed, and hill climbing gained exactly zero - so the solver ranking is structural, not an artifact of the timeout.' If asked in Q&A: we predicted the outcomes before running (full unchanged, hc zero); the one miss was SA, which we expected to gain more - exponential problems shrug at factors of two.

## Slide 12 - Conclusions

~45s. Every claim here is a measured number from experiments/results/results.csv (overall: SA 45/75 = 60%, HC 21/75 = 28%; hard-only: 19/25 vs 11/25). All four members should have spoken by now (equal input is graded).

## Slide 13 - References

Not spoken — present for completeness and Q&A.
