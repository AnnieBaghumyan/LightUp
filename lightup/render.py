"""Terminal rendering of boards.

This is the observability backbone of the project: the CLI, the solver logs
and the step-by-step traces all print boards through this one function, so a
human can always see exactly what the machine is doing.

Glyphs (unicode mode / ascii mode):

    wall             █ / #
    numbered wall    the digit itself (shown inverted when color is on)
    bulb             ◉ / B
    lit white cell   ░ / +
    unlit white cell · / .

Row and column indices are printed on the edges so that log messages like
"place bulb at (3,4)" are easy to follow on the picture.
"""

from .board import lit_cells

# ANSI escape codes (supported by Windows Terminal, VS Code, mac/linux shells).
YELLOW = "\033[93m"
DIM = "\033[2m"
INVERT = "\033[7m"
RESET = "\033[0m"


def render(puzzle, bulbs=frozenset(), *, unicode=True, color=True):
    """Return a printable multi-line picture of the board with the bulbs on it.

    Lighting is recomputed here from the bulb set, so the caller never has to
    pass anything except "where are the bulbs right now".
    """
    bulbs = set(bulbs)
    lit = lit_cells(puzzle, bulbs)

    wall_ch = "█" if unicode else "#"
    bulb_ch = "◉" if unicode else "B"
    lit_ch = "░" if unicode else "+"
    unlit_ch = "·" if unicode else "."

    def paint(text, code):
        return code + text + RESET if color else text

    lines = []
    # Column header (last digit only, keeps the header one character wide).
    lines.append("    " + " ".join(str(c % 10) for c in range(puzzle.width)))

    for r in range(puzzle.height):
        cells = []
        for c in range(puzzle.width):
            n = puzzle.clue(r, c)
            if n is not None:
                cells.append(paint(str(n), INVERT))
            elif puzzle.is_wall(r, c):
                cells.append(wall_ch)
            elif (r, c) in bulbs:
                cells.append(paint(bulb_ch, YELLOW))
            elif (r, c) in lit:
                cells.append(paint(lit_ch, YELLOW))
            else:
                cells.append(paint(unlit_ch, DIM))
        lines.append(f"{r:>3} " + " ".join(cells))

    return "\n".join(lines)
