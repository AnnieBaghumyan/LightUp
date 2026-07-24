# Video script — "compile and run" demo (~4 min)

> Course requirement: a video showing how the code can be compiled and how
> it runs, with a voice-over explaining what is happening.
>
> Record the screen first (Win+G Game Bar or OBS, 1080p), narrate over it
> afterwards — separating the two means a typo or a cough never ruins a
> take. Bump the terminal font to 16-18pt before recording. Commands to
> paste are in the blocks below, in order.

## Before recording (not on camera)

* Fresh terminal in an EMPTY folder (the video should prove setup works
  from nothing).
* `pip install` takes ~1 min — either record it and cut/fast-forward in
  editing, or pre-download wheels once so the on-camera run is fast.
* Have `experiments/results/fig1_bt_scaling.png` open in a photo viewer
  tab, ready to alt-tab to in Scene 7.

---

## Scene 1 — intro (~15 s) · screen: GitHub repo page or the folder

**Voice:** "This is our CS-246 project: the LightUp puzzle — the game
itself, and five AI solvers that compete on it. We'll set it up from
scratch and show it running."

## Scene 2 — setup (~45 s) · screen: terminal

```
git clone https://github.com/AnnieBaghumyan/LightUp.git
cd LightUp
git checkout foundation
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

> NOTE: delete the `git checkout foundation` line once `foundation` is
> merged into `main` — do the merge BEFORE recording (verified 2026-07-24:
> a fresh clone + these commands + the tests all pass on `foundation`).

**Voice:** "Setup is four commands: clone, create a virtual environment,
activate it, and install the two dependencies — pytest for the tests and
matplotlib for the experiment figures. The solver code itself uses only
the Python standard library."
*(Editing: fast-forward the pip output.)*

## Scene 3 — tests (~20 s) · screen: terminal

```
python -m pytest tests/
```

**Voice:** "Fifty-one tests cover the rules engine, the parser, the
generator, and every solver — including a published puzzle whose known
solution our validator must accept. All green."

## Scene 4 — the game (~40 s) · screen: the game window

```
python -m lightup
```

**Voice:** "This opens the game with a random ten-by-ten board. Left
click places a bulb — light spreads until a wall. Right click leaves an
X note, like a human solver. If two bulbs see each other, both are
framed red and the status bar explains the conflict. Clue digits turn
green when satisfied. The bar on top generates new boards — any size
from three to twenty-five, three difficulties."
*(Do on camera: place 2-3 bulbs, one X, create one red conflict, fix it,
then press N for a new board.)*

## Scene 5 — watching the AI think (~45 s) · screen: same window

**Voice:** "Now the AI. We pick the naive backtracking solver and press
Solve. The animation replays every decision: bulbs appear, conflicts
flash red, backtracking removes them — and the status bar counts nodes
in real time. You can pause, single-step, or jump to the end. Now the
same board with full inference — watch: almost everything is deduced in
one cascade, with barely any red. That difference is what our
experiments measure."
*(Do on camera: naive Solve on a 10x10, let it run ~10 s at medium speed,
Stop; switch dropdown to "BT + full inference", Solve, let it finish.)*

## Scene 6 — command line and the headline number (~30 s) · screen: terminal

```
python -m lightup solve puzzles/thesis7x7.txt --solver bt
python -m lightup solve puzzles/thesis7x7.txt --solver full
```

**Voice:** "The same solvers run from the command line with search
statistics. On this published seven-by-seven, naive backtracking needs
three hundred and eight nodes. Full inference needs zero — the whole
puzzle falls to deduction alone."

## Scene 7 — experiments (~25 s) · screen: terminal, then the figure

```
python experiments/run.py --quick
```

**Voice:** "The experiment harness sweeps board sizes, difficulties and
seeds across all five solvers — here a quick sanity sweep; the full one
is three hundred seventy-five runs. It writes a CSV and generates the
figures used in our report — like this scaling comparison."
*(Alt-tab to fig1 for ~5 s.)*

## Scene 8 — outro (~10 s) · screen: the game window or repo

**Voice:** "That's the project: a playable game, five observable
solvers, and a reproducible experiment pipeline. Details and analysis
are in the report. Thanks for watching."

---

## Checklist after recording

- [ ] Every command on screen matches this script (grader may retype them)
- [ ] Voice explains WHAT is happening at each moment (the requirement)
- [ ] Terminal text readable at 1080p playback
- [ ] Length ≤ ~5 min; no dead air during pip install
- [ ] Exported as mp4; check Moodle's size limit before the deadline
