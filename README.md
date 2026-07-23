# LightUp (Akari) — AI Solvers

CS 246 Artificial Intelligence group project (AUA, Summer 2026).

We implement the LightUp puzzle and solve it with several AI techniques from
the course (backtracking CSP search with heuristics and inference, hill
climbing, simulated annealing), then compare and analyze their performance.

## Rules of the game

Place light bulbs on white cells so that:

1. Every white cell is lit. A bulb lights its whole row and column until a
   black wall blocks the light.
2. No two bulbs shine on each other.
3. A numbered wall must have exactly that many bulbs orthogonally adjacent.

## Setup

Requires Python 3.10+ (developed on 3.13). The core code uses only the
standard library; tests use pytest:

```
pip install pytest
```

## Running

From this folder:

```
# Render a puzzle
python -m lightup show puzzles/thesis7x7.txt

# Place bulbs by hand and check them against the rules
python -m lightup check puzzles/corner2.txt --bulbs "0,1 1,0 2,2"

# Plain-terminal fallback
python -m lightup show puzzles/thesis7x7.txt --ascii --no-color
```

## Puzzle file format

One character per cell: `.` white cell, `#` wall, `0`-`4` numbered wall.
The parser also accepts `-` and `*` (the notation used in Pulles, 2021), so
puzzles from the literature can be pasted in unchanged. See `puzzles/`.

## Tests

```
python -m pytest tests/
```

Test fixtures are small hand-checked puzzles; `puzzles/thesis7x7.txt` and its
solution come from Figure 2.1 of B. Pulles, *Analysis of Akari* (2021).

## Project layout

```
lightup/board.py      puzzle representation (immutable givens + geometry)
lightup/parser.py     text <-> Puzzle
lightup/render.py     terminal board rendering
lightup/validator.py  rule checking with named, explained violations
lightup/cli.py        command line interface
puzzles/              puzzle instance files
tests/                pytest suite
```

Solvers, the puzzle generator, the experiment harness and the Tkinter viewer
are added in later steps.
