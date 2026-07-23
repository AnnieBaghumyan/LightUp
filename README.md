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
standard library; pytest (tests) and matplotlib (experiment plots) come from
`requirements.txt`. Use a virtual environment:

```
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Activate the venv (second line) in every new terminal before running the
commands below.

## Running

From this folder:

```
# Render a puzzle
python -m lightup show puzzles/thesis7x7.txt

# Place bulbs by hand and check them against the rules
python -m lightup check puzzles/corner2.txt --bulbs "0,1 1,0 2,2"

# Plain-terminal fallback
python -m lightup show puzzles/thesis7x7.txt --ascii --no-color

# Play the game in a window.
#   left click  = place/remove with the selected tool (Bulb or X)
#   right click = always toggle an X ("no bulb here" note, not validated)
#   keys: B bulb tool, X mark tool, R reset, N new puzzle
# Conflicting cells get a red border, satisfied clues turn green.
# The "New puzzle" bar sets width x height (3-25) and easy/medium/hard.
python -m lightup play puzzles/thesis7x7.txt

# Generate random solvable puzzles (solution-first construction):
python -m lightup generate 10x10 --seed 7                  # print it
python -m lightup generate 10x10 --difficulty hard         # preset density
python -m lightup generate 10x10 --seed 7 --out my.txt     # save it
python -m lightup generate 12x12 --play                    # play it now
# fine knobs: --walls 0.18 --clues 0.85 --no-symmetry --show-solution
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
lightup/gui.py        Tkinter hand-play window (BoardView + PlayApp)
lightup/generator.py  random solvable puzzles (solution-first construction)
puzzles/              puzzle instance files
tests/                pytest suite
```

Solvers, the puzzle generator and the experiment harness are added in later
steps; the GUI's `BoardView.show_state()` is the hook their step-by-step
animation will use.
