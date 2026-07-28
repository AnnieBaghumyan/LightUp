# Report correction list

Mechanical fixes to apply in the Overleaf source. Line numbers refer to
`docs/report.tex`; the same text is easy to find in Overleaf.

> Note: `docs/report.tex` in this repo has lost every backslash
> (`documentclass`, `usepackage`, …) and will not compile. Overleaf holds
> the working source — fix there, and re-export a clean copy afterwards.

## 1. Spelling and grammar

| where | current | corrected |
|---|---|---|
| Abstract | japanese | Japanese |
| §1.1 | three full books consisted of only | consisting of only |
| §1.2 | illuminating it's entire row | its entire row |
| §1.2 | no two bulb should be | no two bulbs should be |
| §1.2 | unless block from each other | unless blocked from each other |
| §2.1 | using a an approach | using an approach |
| §2.1 | hill climbing wiht optimized | with |
| §2.2 | executed a tirivial solver | trivial |
| §2.2 | 40 × 40 boars | boards |
| §3.2 | Both solver share | Both solvers share |
| §3.2 | They navogate the search space | navigate |
| §3.2 | a more sturctured starting point | structured |
| §3.2 | the cost function that the agents works | the agent works |
| §3.2 | search initally starts | initially |
| §3.2.2 | the agent is very frequently jumps | the agent very frequently jumps |
| §3.2.2 | becoming more liks regular | more like regular |

## 2. Broken LaTeX references (these print as `??`)

* `Section~\ref{sec:csp}` (§3.1.1) has no target — add `\label{sec:csp}`
  immediately after `\section{CSP}`.
* `Chapter~\ref{chap:results}` (§3.1.3) has no target — add
  `\label{chap:results}` immediately after `\chapter{Results}`.
* `$\text{Eq.}~(4)$` (§3.1.1) points to an equation that does not exist:
  the equations in the report are (3.1)–(3.3), and the doomed-cell rule
  is never formally stated anywhere. Either state it as an equation in
  §3.1 and reference that label, or reword the sentence so it does not
  claim the rule was stated earlier. **Your call — it needs your words.**

## 3. Contradiction in §1.2

"a rectangular N × N sized board" — rectangular and $N \times N$ are not
the same thing. Decide which you mean (the code supports rectangular; all
experiments used square boards) and say it accordingly.

## 4. Missing bibliography entries

The report currently cites two sources. These three are referenced by the
content but not listed; paste into `thebibliography` and cite in the text
where relevant (NP-completeness in the Introduction, AIMA wherever the
standard algorithms are named, Nikoli for the §1.1 publication claim).

```latex
\bibitem{mcphail}
McPhail, B., ``Light Up is NP-complete'', 2005,
\href{https://www.researchgate.net/publication/249927572_Light_Up_is_NP-complete}{researchgate.net/publication/249927572}

\bibitem{aima}
Russell, S., Norvig, P., \emph{Artificial Intelligence: A Modern
Approach}, 4th ed., Pearson, 2021.

\bibitem{nikoli}
Nikoli, ``Light Up (Bijutsukan)'',
\href{https://www.nikoli.co.jp/en/puzzles/akari/}{nikoli.co.jp/en/puzzles/akari}
```

Also check the two existing `\href` targets: in the exported copy they
read `httpswww.cs.ru.nl...` and `httpsarxiv.orgpdf2107.10429` (missing
`://` and `/`). Verify they are correct in Overleaf.

## 5. Result tables

`experiments/tables.py` generates LaTeX tables straight from the CSVs, so
the numbers in the report come from the same pipeline as the figures:

```
python experiments/tables.py > tables.tex          # all six tables
python experiments/tables.py --which solve_size    # just one
```

Tables available: `solve_size`, `solve_diff`, `nodes`, `time`, `fcfull`,
`budget`. Captions are deliberately left as a placeholder comment —
write your own, and put them **below** the table (guideline 7).

## 6. Figures you have but have not used

All four are in `experiments/results/` and none appear in the report yet:

| file | shows |
|---|---|
| `fig1_bt_scaling.png` | nodes and time vs board size, three BT variants |
| `fig2_paradigms.png` | solve rate vs size, all five solvers |
| `fig3_difficulty.png` | median time by difficulty preset at 14×14 |
| `fig4_budget.png` | solve rate under 5 s vs 10 s budgets |

Inclusion pattern matching the ones already in the report:

```latex
\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\linewidth]{fig1_bt_scaling.png}
    \caption{WRITE YOUR OWN CAPTION}
    \label{fig:scaling}
\end{figure}
```

Every figure must be referred to in the text (guideline 9).

## 7. Content still to write (yours)

Not fixable mechanically — these are the parts that carry the marks:

1. **§4.1, third paragraph is factually inverted.** In your generator
   `hard` = 12 % walls / 55 % clued (*fewest* clues) and `easy` = 25 % /
   100 % (*most* clues). Hill climbing did better on the sparse boards
   (11/25 hard vs 5/25 easy), and the reason is the opposite of what the
   paragraph says. See `report-notes.md` §R7.
2. **A `\section{Experimental setup}`** in Chapter 3: the generator, 5
   sizes × 3 difficulties × 5 seeds = 75 instances, identical instances
   per solver, 5 s budget, seeds fixed, correctness judged by the
   validator rather than against a stored answer.
3. **Chapter 4 rebuilt around the tables and figures**, including the
   results you measured but have not reported (fc-vs-full by difficulty,
   `best_cost` on failures, the zero-search published puzzle) and the
   caveats (5 seeds per bucket; medians over solved runs only, which is
   why the naive-BT node median dips at 18×18).
4. **§4.2 Conclusion and §4.3 Future work** — currently `conclusion` and
   `blablabla`.
5. **A linking paragraph** at the end of Chapter 2 relating the two
   papers to your own work.
6. **Word count**: roughly 4 100–4 300 now against a 3 000 limit, and
   Chapter 4 still needs to grow. Cut Chapter 2 (~1 000 words for two
   papers) and tighten Chapter 3.

Material for all six is in `report-notes.md` — arguments and numbers to
work from, not text to copy.
