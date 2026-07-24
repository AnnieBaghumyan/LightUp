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

import threading
import tkinter as tk
from tkinter import filedialog, ttk, font as tkfont
from pathlib import Path

from . import parser as puzzle_parser
from .board import lit_cells
from .generator import DIFFICULTY, MAX_SIZE, MIN_SIZE, generate
from .solvers import SOLVERS
from .validator import check_solution, involved_cells

SOLVE_TIMEOUT_S = 15  # keep the recording bounded on hard boards

# ----- look & feel -----------------------------------------------------------

CELL = 52      # preferred pixel size of one board cell (small boards)
MIN_CELL = 20  # floor when shrinking big boards to fit the screen
PAD = 18       # margin around the board inside the canvas

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
    "mark":       "#8a8a94",  # player's X = "no bulb here" note
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
        """Attach a (new) puzzle and resize the canvas to fit it.

        The cell size adapts to the screen: big boards (up to 25x25) shrink
        until they fit, small boards use the comfortable default.  The
        margins subtracted below leave room for the toolbars, the status
        bar and the OS taskbar.
        """
        self.puzzle = puzzle
        avail_w = self.canvas.winfo_screenwidth() - 120 - 2 * PAD
        avail_h = self.canvas.winfo_screenheight() - 280 - 2 * PAD
        self.cell = max(MIN_CELL,
                        min(CELL, avail_w // puzzle.width,
                            avail_h // puzzle.height))
        self.canvas.config(width=puzzle.width * self.cell + 2 * PAD,
                           height=puzzle.height * self.cell + 2 * PAD)

    def cell_at(self, x, y):
        """The (row, col) under a pixel position, or None outside the board."""
        c = (x - PAD) // self.cell
        r = (y - PAD) // self.cell
        return (r, c) if self.puzzle.in_bounds(r, c) else None

    # ----- drawing -----------------------------------------------------------

    def _cell_box(self, r, c):
        """Pixel rectangle (x0, y0, x1, y1) of a cell."""
        x0 = PAD + c * self.cell
        y0 = PAD + r * self.cell
        return x0, y0, x0 + self.cell, y0 + self.cell

    def _draw_bulb(self, r, c, in_conflict):
        """A bulb drawn as shapes (not an emoji) so it looks the same on
        every machine: a glowing circle with four short rays."""
        x0, y0, x1, y1 = self._cell_box(r, c)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        radius = self.cell * 0.26
        ray_in, ray_out = self.cell * 0.32, self.cell * 0.44
        edge = COLORS["conflict"] if in_conflict else COLORS["bulb_edge"]
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            self.canvas.create_line(cx + dx * ray_in, cy + dy * ray_in,
                                    cx + dx * ray_out, cy + dy * ray_out,
                                    fill=edge, width=2)
        self.canvas.create_oval(cx - radius, cy - radius,
                                cx + radius, cy + radius,
                                fill=COLORS["bulb"], outline=edge, width=2)

    def _draw_mark(self, r, c):
        """The player's X note: "I believe no bulb goes here".  Purely a
        convenience for the human — the validator never sees the marks."""
        x0, y0, x1, y1 = self._cell_box(r, c)
        inset = self.cell * 0.32
        width = max(2, self.cell // 16)
        self.canvas.create_line(x0 + inset, y0 + inset, x1 - inset, y1 - inset,
                                fill=COLORS["mark"], width=width,
                                capstyle="round")
        self.canvas.create_line(x0 + inset, y1 - inset, x1 - inset, y0 + inset,
                                fill=COLORS["mark"], width=width,
                                capstyle="round")

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

    def show_state(self, bulbs, conflicts=frozenset(), solved=False,
                   marks=frozenset()):
        """Repaint the board for the given bulb set.

        conflicts: cells to outline in red (computed by the caller from the
        validator's violations, so the view itself knows no game rules).
        marks: the player's X notes, drawn but never validated.
        """
        puzzle = self.puzzle
        lit = lit_cells(puzzle, bulbs)
        self.canvas.delete("all")

        clue_font = tkfont.Font(family="Segoe UI",
                                size=max(8, self.cell // 3), weight="bold")

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
                elif (r, c) in marks:
                    self._draw_mark(r, c)

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


class ToolButton(tk.Canvas):
    """A small icon button for the left-click tool selector.

    The icons are drawn with the same shapes the board uses (glowing bulb,
    gray X), so the buttons read as "what will appear on the board when I
    click".  The selected tool gets a yellow accent border.  Drawn on a
    canvas instead of using emoji/image files so it looks identical on
    every machine.
    """

    SIZE = 36

    def __init__(self, parent, variable, value, icon):
        super().__init__(parent, width=self.SIZE, height=self.SIZE,
                         bg="#33333e", highlightthickness=2, cursor="hand2")
        self.variable, self.value = variable, value
        self.bind("<Button-1>", lambda _e: variable.set(value))
        # Restyle whenever the tool changes, including via the B/X keys.
        variable.trace_add("write", lambda *_: self._restyle())
        self._draw(icon)
        self._restyle()

    def _draw(self, icon):
        s = self.SIZE / 2 + 1  # visual center (canvas border offset)
        if icon == "bulb":
            radius, ray_in, ray_out = 8, 11, 15
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                self.create_line(s + dx * ray_in, s + dy * ray_in,
                                 s + dx * ray_out, s + dy * ray_out,
                                 fill=COLORS["bulb_edge"], width=2)
            self.create_oval(s - radius, s - radius, s + radius, s + radius,
                             fill=COLORS["bulb"], outline=COLORS["bulb_edge"],
                             width=2)
        else:  # the X mark
            inset = 11
            for x0, x1 in [(s - inset, s + inset), (s + inset, s - inset)]:
                self.create_line(x0, s - inset, x1, s + inset,
                                 fill=COLORS["mark"], width=3,
                                 capstyle="round")

    def _restyle(self):
        selected = self.variable.get() == self.value
        accent = COLORS["bulb"] if selected else "#44444f"
        self.configure(highlightbackground=accent, highlightcolor=accent)


class PlayApp:
    """The hand-play window: click white cells to place/remove bulbs."""

    def __init__(self, root, puzzle, title="LightUp"):
        self.root = root
        self.bulbs = set()
        self.marks = set()   # the player's X notes ("no bulb here")

        # Solver-animation state.  The solver runs in a background thread
        # while an observer records its events; the GUI then REPLAYS the
        # recording (play/pause/step/finish) by maintaining the bulb set
        # incrementally from the events.  self.replay is None in hand-play
        # mode, else {"events", "pos", "bulbs", "result"}.
        self.replay = None
        self.solving = False
        self.playing = False
        self._on_ready = None   # action to run when the recording is ready

        root.title("LightUp — Akari")
        root.configure(bg=COLORS["app_bg"])
        root.resizable(False, False)

        ui_font = tkfont.Font(family="Segoe UI", size=10)
        button_style = dict(font=ui_font, bg="#33333e", fg=COLORS["white"],
                            activebackground="#44444f",
                            activeforeground=COLORS["white"],
                            relief="flat", padx=10)

        # --- toolbar: puzzle name, tool selector, buttons -------------------
        toolbar = tk.Frame(root, bg=COLORS["app_bg"])
        toolbar.pack(fill="x", padx=12, pady=(10, 4))
        self.title_label = tk.Label(toolbar, text=title, font=ui_font,
                                    bg=COLORS["app_bg"],
                                    fg=COLORS["status_txt"])
        self.title_label.pack(side="left")

        # Tool selector: what a LEFT click places.  Right click is always X.
        # Icon buttons drawn with the same shapes the board uses.
        self.tool = tk.StringVar(value="bulb")
        for value in ["mark", "bulb"]:
            ToolButton(toolbar, self.tool, value,
                       icon=value if value == "bulb" else "x"
                       ).pack(side="right", padx=(6, 0))
        for text, command in [("Reset (R)", self.reset),
                              ("Open…", self.open_file)]:
            tk.Button(toolbar, text=text, command=command,
                      **button_style).pack(side="right", padx=(6, 0))

        # --- new-puzzle configuration: size (3-25) and difficulty -----------
        config = tk.Frame(root, bg=COLORS["app_bg"])
        config.pack(fill="x", padx=12, pady=(0, 4))
        tk.Label(config, text="New puzzle:", font=ui_font,
                 bg=COLORS["app_bg"], fg=COLORS["status_txt"]
                 ).pack(side="left")

        self.width_var = tk.IntVar(value=puzzle.width)
        self.height_var = tk.IntVar(value=puzzle.height)
        spin_style = dict(from_=MIN_SIZE, to=MAX_SIZE, width=3, font=ui_font,
                          bg="#33333e", fg=COLORS["white"],
                          buttonbackground="#44444f", relief="flat",
                          justify="center")
        tk.Spinbox(config, textvariable=self.width_var,
                   **spin_style).pack(side="left", padx=(8, 2))
        tk.Label(config, text="×", font=ui_font, bg=COLORS["app_bg"],
                 fg=COLORS["status_txt"]).pack(side="left")
        tk.Spinbox(config, textvariable=self.height_var,
                   **spin_style).pack(side="left", padx=(2, 8))

        self.difficulty_var = tk.StringVar(value="medium")
        difficulty = ttk.Combobox(config, textvariable=self.difficulty_var,
                                  values=list(DIFFICULTY), state="readonly",
                                  width=8, font=ui_font)
        difficulty.pack(side="left", padx=(0, 8))

        tk.Button(config, text="Generate (N)", command=self.new_puzzle,
                  **button_style).pack(side="left")

        # --- solver panel: pick a solver and watch it think -----------------
        solver_bar = tk.Frame(root, bg=COLORS["app_bg"])
        solver_bar.pack(fill="x", padx=12, pady=(0, 4))
        tk.Label(solver_bar, text="Solver:", font=ui_font,
                 bg=COLORS["app_bg"], fg=COLORS["status_txt"]
                 ).pack(side="left")
        self.solver_var = tk.StringVar(value=next(iter(SOLVERS)))
        ttk.Combobox(solver_bar, textvariable=self.solver_var,
                     values=list(SOLVERS), state="readonly", width=19,
                     font=ui_font).pack(side="left", padx=(8, 8))
        for text, command in [("Solve", self.start_solve),
                              ("Play/Pause", self.toggle_play),
                              ("Step", self.step_once),
                              ("Finish", self.finish_replay),
                              ("Stop", self.stop_replay)]:
            tk.Button(solver_bar, text=text, command=command,
                      **button_style).pack(side="left", padx=(0, 6))
        tk.Label(solver_bar, text="speed", font=ui_font,
                 bg=COLORS["app_bg"], fg=COLORS["status_txt"]
                 ).pack(side="left", padx=(6, 2))
        self.speed_var = tk.IntVar(value=80)  # solver events per second
        tk.Scale(solver_bar, variable=self.speed_var, from_=10, to=1000,
                 orient="horizontal", showvalue=False, length=110,
                 bg=COLORS["app_bg"], troughcolor="#33333e",
                 highlightthickness=0).pack(side="left")

        # --- board ----------------------------------------------------------
        self.view = BoardView(root, puzzle)
        self.view.canvas.pack(padx=12, pady=4)
        self.view.canvas.bind("<Button-1>", self.on_click)
        self.view.canvas.bind("<Button-3>", self.on_right_click)
        root.bind("r", lambda _e: self.reset())
        root.bind("R", lambda _e: self.reset())
        root.bind("n", lambda _e: self.new_puzzle())
        root.bind("N", lambda _e: self.new_puzzle())
        root.bind("b", lambda _e: self.tool.set("bulb"))
        root.bind("B", lambda _e: self.tool.set("bulb"))
        root.bind("x", lambda _e: self.tool.set("mark"))
        root.bind("X", lambda _e: self.tool.set("mark"))

        # --- status bar -----------------------------------------------------
        self.status = tk.Label(root, font=ui_font, bg=COLORS["app_bg"],
                               fg=COLORS["status_txt"], anchor="w",
                               justify="left")
        self.status.pack(fill="x", padx=14, pady=(2, 10))

        self.refresh()

    # ----- solver animation --------------------------------------------------

    def start_solve(self, on_ready=None):
        """Run the selected solver in a background thread, recording its
        observer events; when it finishes, animate the recording.

        on_ready: optional action to run instead of auto-playing once the
        recording exists (used by Step and Finish when pressed cold).
        """
        if self.solving:
            return
        self._on_ready = on_ready
        self.stop_replay()
        self.bulbs.clear()
        self.marks.clear()
        self.solving = True
        self.status.config(text="Solving (recording the search)…",
                           fg=COLORS["status_txt"])

        events = []
        holder = {}
        solver = SOLVERS[self.solver_var.get()]
        puzzle = self.view.puzzle

        def run():  # solver thread: touches only its own data
            holder["result"] = solver(
                puzzle,
                observer=lambda ev, cell, bulbs: events.append((ev, cell)),
                timeout_s=SOLVE_TIMEOUT_S)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        self._await_solver(thread, events, holder)

    def _await_solver(self, thread, events, holder):
        """Poll from the Tk main loop until the solver thread is done."""
        if thread.is_alive():
            self.root.after(100, lambda: self._await_solver(
                thread, events, holder))
            return
        self.solving = False
        # After the first solution the recursion unwinds, emitting "remove"
        # events as the stack pops — cut the recording at the solution so
        # the replay ends ON the solved board instead of un-building it.
        for i, (ev, _cell) in enumerate(events):
            if ev == "solution":
                del events[i + 1:]
                break
        self.replay = {"events": events, "pos": 0, "bulbs": set(),
                       "result": holder["result"]}
        self.playing = False
        if self._on_ready is not None:
            action, self._on_ready = self._on_ready, None
            action()            # e.g. Step or Finish pressed before Solve
        else:
            self.toggle_play()  # default: start the animation immediately

    def _advance(self, n):
        """Replay the next n recorded events onto the board."""
        rp = self.replay
        if rp is None:
            return
        conflicts = set()
        last = ""
        solved_now = False
        while n > 0 and rp["pos"] < len(rp["events"]):
            ev, cell = rp["events"][rp["pos"]]
            rp["pos"] += 1
            n -= 1
            if ev == "place":
                rp["bulbs"].add(cell)
            elif ev == "remove":
                rp["bulbs"].discard(cell)
            elif ev == "conflict":
                conflicts.add(cell)   # flashes red for this frame
            elif ev == "solution":
                solved_now = True
            last = ev if cell is None else f"{ev} {cell}"

        self.view.show_state(rp["bulbs"], conflicts, solved_now)

        result, stats = rp["result"], rp["result"].stats
        progress = (f"solver: event {rp['pos']}/{len(rp['events'])}"
                    f"   [{last}]")
        totals = (f"nodes={stats.nodes}  conflicts={stats.conflicts}  "
                  f"backtracks={stats.backtracks}  "
                  f"time={stats.time_ms:.0f}ms")
        if rp["pos"] >= len(rp["events"]):     # recording fully replayed
            self.playing = False
            if result.solved:
                verdict = "SOLVED"
            elif result.timed_out:
                verdict = f"TIMED OUT after {SOLVE_TIMEOUT_S}s"
            else:
                verdict = "NO SOLUTION exists"
            self.status.config(
                text=f"{verdict} — {totals}",
                fg=COLORS["status_ok"] if result.solved
                else COLORS["status_txt"])
        else:
            self.status.config(text=f"{progress}\n{totals}",
                               fg=COLORS["status_txt"])
        if solved_now:
            self.playing = False               # pause on the solution frame

    def _rewind(self):
        """Reset the recording to the start so it can be watched again."""
        self.replay["pos"] = 0
        self.replay["bulbs"] = set()

    def toggle_play(self):
        if self.solving:
            return
        if self.replay is None:
            self.start_solve()      # pressed cold: solve, then auto-play
            return
        if self.replay["pos"] >= len(self.replay["events"]):
            self._rewind()          # finished recording: play it again
            self.playing = False
        self.playing = not self.playing
        if self.playing:
            self._play_tick()

    def _play_tick(self):
        """Animation heartbeat: every 25ms replay a batch of events sized
        by the speed slider (events per second)."""
        if not self.playing or self.replay is None:
            return
        self._advance(max(1, self.speed_var.get() // 40))
        if self.playing:
            self.root.after(25, self._play_tick)

    def step_once(self):
        if self.solving:
            return
        if self.replay is None:
            # Pressed cold: record first, then take the first step (paused).
            self.start_solve(on_ready=self.step_once)
            return
        self.playing = False
        if self.replay["pos"] >= len(self.replay["events"]):
            self._rewind()          # stepping past the end starts over
        self._advance(1)

    def finish_replay(self):
        """Jump straight to the end of the recording."""
        if self.solving:
            return
        if self.replay is None:
            self.start_solve(on_ready=self.finish_replay)
            return
        self.playing = False
        self._advance(len(self.replay["events"]))

    def stop_replay(self):
        """Leave solver mode and return the board to hand-play."""
        self.playing = False
        if self.replay is not None:
            self.replay = None
            self.refresh()

    # ----- interaction -------------------------------------------------------

    def on_click(self, event):
        """Left click: place/remove whatever the selected tool is."""
        if self.solving:
            return                 # hands off while the solver is recording
        if self.replay is not None:
            self.stop_replay()     # first click exits solver mode
            return
        cell = self.view.cell_at(event.x, event.y)
        if cell is None or not self.view.puzzle.is_white(*cell):
            return  # clicks on walls or the margin do nothing
        if self.tool.get() == "bulb":
            self._toggle(cell, self.bulbs, also_clear=self.marks)
        else:
            self._toggle(cell, self.marks, also_clear=self.bulbs)

    def on_right_click(self, event):
        """Right click: always toggle an X mark, regardless of the tool."""
        if self.solving or self.replay is not None:
            return
        cell = self.view.cell_at(event.x, event.y)
        if cell is None or not self.view.puzzle.is_white(*cell):
            return
        self._toggle(cell, self.marks, also_clear=self.bulbs)

    def _toggle(self, cell, target, also_clear):
        """Toggle `cell` in `target`; a cell never holds a bulb AND an X."""
        if cell in target:
            target.remove(cell)
        else:
            target.add(cell)
            also_clear.discard(cell)
        self.refresh()

    def reset(self):
        self.stop_replay()
        self.bulbs.clear()
        self.marks.clear()
        self.refresh()

    def new_puzzle(self):
        """Generate a random puzzle from the size/difficulty configuration."""
        # Spinboxes allow typing, so clamp whatever is in them to the range.
        try:
            width = min(MAX_SIZE, max(MIN_SIZE, self.width_var.get()))
            height = min(MAX_SIZE, max(MIN_SIZE, self.height_var.get()))
        except tk.TclError:   # non-numeric text typed into a spinbox
            width, height = self.view.puzzle.width, self.view.puzzle.height
        self.width_var.set(width)
        self.height_var.set(height)
        level = self.difficulty_var.get()

        puzzle, _solution = generate(height, width, **DIFFICULTY[level])
        self.view.set_puzzle(puzzle)
        self.title_label.config(text=f"generated {width}x{height} ({level})")
        self.reset()

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
        if self.replay is not None:
            return  # the replay owns the canvas while it is active
        puzzle = self.view.puzzle
        violations = check_solution(puzzle, self.bulbs)
        solved = not violations
        conflicts = involved_cells(violations, CONFLICT_KINDS)

        self.view.show_state(self.bulbs, conflicts, solved, marks=self.marks)

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


def run_puzzle(puzzle, title="LightUp"):
    """Open the hand-play window for an in-memory puzzle."""
    root = tk.Tk()
    PlayApp(root, puzzle, title=title)
    root.mainloop()


def run(puzzle_path):
    """Open the hand-play window for one puzzle file (CLI entry point)."""
    run_puzzle(puzzle_parser.parse_file(puzzle_path),
               title=Path(puzzle_path).name)
