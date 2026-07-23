"""Tkinter viewer and hand-play mode for LightUp puzzles.

Design (mirrors the agent/environment separation from the report):

- All rules live in the validator; this file only *draws* and forwards
  clicks.  The GUI can never disagree with the CLI about what is legal.
- `BoardView` is a "dumb" painter: you hand it the current bulb set via
  show_state() and it repaints the whole board.  Today the mouse feeds it;
  in a later step the solvers' observer callbacks will feed it the same
  way, which gives us step-by-step solver animation without rewriting
  anything here.
- `PlayApp` wires BoardView to mouse clicks, toolbar buttons and a status
  bar.

Run with:

    python -m lightup play puzzles/thesis7x7.txt
"""

import tkinter as tk
from tkinter import filedialog, font as tkfont
from pathlib import Path

from . import parser as puzzle_parser
from .board import lit_cells
from .validator import check_solution, involved_cells

# ----- look & feel -----------------------------------------------------------

CELL = 52   # pixel size of one board cell
PAD = 18    # margin around the board inside the canvas

COLORS = {
    "app_bg":     "#23232b",  # window background
    "board_bg":   "#1a1a21",  # canvas background around the cells
    "white":      "#f7f4ec",  # unlit white cell
    "lit":        "#ffe08a",  # illuminated cell
    "wall":       "#101014",  # black wall
    "grid":       "#3a3a44",  # thin lines between cells
    "bulb":       "#ffd23f",  # bulb body
    "bulb_edge":  "#8a6d00",
    "conflict":   "#e4572e",  # border of cells involved in a violation
    "clue_text":  "#f7f4ec",  # clue still open
    "clue_ok":    "#8fd694",  # clue satisfied exactly
    "clue_bad":   "#ff6b6b",  # clue exceeded or impossible
    "status_ok":  "#8fd694",
    "status_txt": "#d8d4c8",
}

# Violations whose cells we outline in red.  Deliberately NOT "cell_unlit":
# while playing, most of the board is unlit, and painting it all red would
# drown the real mistakes.
CONFLICT_KINDS = {"bulbs_see_each_other", "clue_exceeded",
                  "clue_unsatisfiable", "bulb_not_on_white"}


class BoardView:
    """Draws a puzzle plus a bulb placement on a Tkinter canvas.

    The single entry point is show_state(); it repaints everything from
    scratch.  A full repaint is simple to reason about and easily fast
    enough for our board sizes.
    """

    def __init__(self, parent, puzzle):
        self.canvas = tk.Canvas(parent, bg=COLORS["board_bg"],
                                highlightthickness=0)
        self.set_puzzle(puzzle)

    def set_puzzle(self, puzzle):
        """Attach a (new) puzzle and resize the canvas to fit it."""
        self.puzzle = puzzle
        self.canvas.config(width=puzzle.width * CELL + 2 * PAD,
                           height=puzzle.height * CELL + 2 * PAD)

    def cell_at(self, x, y):
        """The (row, col) under a pixel position, or None outside the board."""
        c = (x - PAD) // CELL
        r = (y - PAD) // CELL
        return (r, c) if self.puzzle.in_bounds(r, c) else None

    # ----- drawing -----------------------------------------------------------

    def _cell_box(self, r, c):
        """Pixel rectangle (x0, y0, x1, y1) of a cell."""
        x0 = PAD + c * CELL
        y0 = PAD + r * CELL
        return x0, y0, x0 + CELL, y0 + CELL

    def _draw_bulb(self, r, c, in_conflict):
        """A bulb drawn as shapes (not an emoji) so it looks the same on
        every machine: a glowing circle with four short rays."""
        x0, y0, x1, y1 = self._cell_box(r, c)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        radius = CELL * 0.26
        ray_in, ray_out = radius + 3, radius + 9
        edge = COLORS["conflict"] if in_conflict else COLORS["bulb_edge"]
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            self.canvas.create_line(cx + dx * ray_in, cy + dy * ray_in,
                                    cx + dx * ray_out, cy + dy * ray_out,
                                    fill=edge, width=2)
        self.canvas.create_oval(cx - radius, cy - radius,
                                cx + radius, cy + radius,
                                fill=COLORS["bulb"], outline=edge, width=2)

    def _clue_color(self, r, c, bulbs):
        """Clue digit color: green when satisfied exactly, red when already
        over the limit, neutral otherwise."""
        n = self.puzzle.clue(r, c)
        placed = sum(1 for cell in self.puzzle.white_neighbors(r, c)
                     if cell in bulbs)
        if placed > n:
            return COLORS["clue_bad"]
        if placed == n:
            return COLORS["clue_ok"]
        return COLORS["clue_text"]

    def show_state(self, bulbs, conflicts=frozenset(), solved=False):
        """Repaint the board for the given bulb set.

        conflicts: cells to outline in red (computed by the caller from the
        validator's violations, so the view itself knows no game rules).
        """
        puzzle = self.puzzle
        lit = lit_cells(puzzle, bulbs)
        self.canvas.delete("all")

        clue_font = tkfont.Font(family="Segoe UI", size=CELL // 3,
                                weight="bold")

        for r in range(puzzle.height):
            for c in range(puzzle.width):
                x0, y0, x1, y1 = self._cell_box(r, c)
                if puzzle.is_wall(r, c):
                    fill = COLORS["wall"]
                elif (r, c) in lit:
                    fill = COLORS["lit"]
                else:
                    fill = COLORS["white"]
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill,
                                             outline=COLORS["grid"])

                n = puzzle.clue(r, c)
                if n is not None:
                    self.canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2,
                                            text=str(n), font=clue_font,
                                            fill=self._clue_color(r, c, bulbs))
                elif (r, c) in bulbs:
                    self._draw_bulb(r, c, (r, c) in conflicts)

                if (r, c) in conflicts:
                    self.canvas.create_rectangle(x0 + 1, y0 + 1, x1 - 1, y1 - 1,
                                                 outline=COLORS["conflict"],
                                                 width=3)

        if solved:
            self._draw_solved_banner()

    def _draw_solved_banner(self):
        """A dimmed overlay with a big SOLVED message."""
        w = int(self.canvas["width"])
        h = int(self.canvas["height"])
        # stipple gives a see-through effect (Canvas has no real transparency)
        self.canvas.create_rectangle(0, h / 2 - 42, w, h / 2 + 42,
                                     fill="#101014", stipple="gray75",
                                     outline="")
        banner_font = tkfont.Font(family="Segoe UI", size=26, weight="bold")
        self.canvas.create_text(w / 2, h / 2, text="✨ SOLVED ✨",
                                font=banner_font, fill=COLORS["clue_ok"])


class PlayApp:
    """The hand-play window: click white cells to place/remove bulbs."""

    def __init__(self, root, puzzle, title="LightUp"):
        self.root = root
        self.bulbs = set()

        root.title("LightUp — Akari")
        root.configure(bg=COLORS["app_bg"])
        root.resizable(False, False)

        ui_font = tkfont.Font(family="Segoe UI", size=10)

        # --- toolbar: puzzle name + buttons ---------------------------------
        toolbar = tk.Frame(root, bg=COLORS["app_bg"])
        toolbar.pack(fill="x", padx=12, pady=(10, 4))
        self.title_label = tk.Label(toolbar, text=title, font=ui_font,
                                    bg=COLORS["app_bg"],
                                    fg=COLORS["status_txt"])
        self.title_label.pack(side="left")
        for text, command in [("Reset (R)", self.reset), ("Open…", self.open_file)]:
            tk.Button(toolbar, text=text, command=command, font=ui_font,
                      bg="#33333e", fg=COLORS["white"],
                      activebackground="#44444f",
                      activeforeground=COLORS["white"],
                      relief="flat", padx=10).pack(side="right", padx=(6, 0))

        # --- board ----------------------------------------------------------
        self.view = BoardView(root, puzzle)
        self.view.canvas.pack(padx=12, pady=4)
        self.view.canvas.bind("<Button-1>", self.on_click)
        root.bind("r", lambda _e: self.reset())
        root.bind("R", lambda _e: self.reset())

        # --- status bar -----------------------------------------------------
        self.status = tk.Label(root, font=ui_font, bg=COLORS["app_bg"],
                               fg=COLORS["status_txt"], anchor="w",
                               justify="left")
        self.status.pack(fill="x", padx=14, pady=(2, 10))

        self.refresh()

    # ----- interaction -------------------------------------------------------

    def on_click(self, event):
        cell = self.view.cell_at(event.x, event.y)
        if cell is None or not self.view.puzzle.is_white(*cell):
            return  # clicks on walls or the margin do nothing
        if cell in self.bulbs:
            self.bulbs.remove(cell)
        else:
            self.bulbs.add(cell)
        self.refresh()

    def reset(self):
        self.bulbs.clear()
        self.refresh()

    def open_file(self):
        path = filedialog.askopenfilename(
            title="Open a LightUp puzzle",
            initialdir=Path(__file__).resolve().parent.parent / "puzzles",
            filetypes=[("Puzzle files", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        self.view.set_puzzle(puzzle_parser.parse_file(path))
        self.title_label.config(text=Path(path).name)
        self.reset()

    # ----- state -> screen ---------------------------------------------------

    def refresh(self):
        """Recompute everything from the validator and repaint."""
        puzzle = self.view.puzzle
        violations = check_solution(puzzle, self.bulbs)
        solved = not violations
        conflicts = involved_cells(violations, CONFLICT_KINDS)

        self.view.show_state(self.bulbs, conflicts, solved)

        lit = lit_cells(puzzle, self.bulbs)
        total = len(puzzle.white_cells())
        rule_breaks = [v for v in violations if v.kind in CONFLICT_KINDS]
        if solved:
            self.status.config(text="Solved — all cells lit, all clues exact.",
                               fg=COLORS["status_ok"])
        else:
            text = (f"Bulbs: {len(self.bulbs)}    "
                    f"Lit: {len(lit)}/{total}    "
                    f"Rule breaks: {len(rule_breaks)}")
            if rule_breaks:
                text += f"\n⚠ {rule_breaks[0].message}"
            self.status.config(text=text, fg=COLORS["status_txt"])


def run(puzzle_path):
    """Open the hand-play window for one puzzle file (CLI entry point)."""
    puzzle = puzzle_parser.parse_file(puzzle_path)
    root = tk.Tk()
    PlayApp(root, puzzle, title=Path(puzzle_path).name)
    root.mainloop()
