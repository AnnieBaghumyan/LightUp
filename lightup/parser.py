"""Reading and writing LightUp puzzles in a plain-text grid format.

One character per cell:

    .    white cell                 (we also accept '-', used in Pulles 2021)
    #    wall without a number      (we also accept '*', used in Pulles 2021)
    0-4  wall with a clue

Example of a full 3x3 puzzle file:

    2..
    ...
    ...

Accepting the alternative glyphs means puzzles printed in the literature can
be pasted into our files unchanged.
"""

from .board import Puzzle, EMPTY, WALL, CLUE_CHARS

# Other authors' glyphs mapped onto ours.
ALIASES = {"-": EMPTY, "*": WALL}
VALID_CHARS = set(EMPTY + WALL + CLUE_CHARS)


def parse(text):
    """Turn a grid string into a Puzzle.  Raises ValueError on bad input."""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue  # allow blank lines around/inside the file
        rows.append("".join(ALIASES.get(ch, ch) for ch in line))

    if not rows:
        raise ValueError("puzzle text contains no grid lines")

    for i, row in enumerate(rows):
        if len(row) != len(rows[0]):
            raise ValueError(
                f"row {i} has {len(row)} cells, expected {len(rows[0])} "
                "(all rows must have equal length)")
        for j, ch in enumerate(row):
            if ch not in VALID_CHARS:
                raise ValueError(
                    f"invalid character {ch!r} at row {i}, column {j}")

    return Puzzle(rows)


def parse_file(path):
    """Read a puzzle from a text file."""
    with open(path, encoding="utf-8") as f:
        return parse(f.read())


def to_text(puzzle):
    """Inverse of parse(): the canonical text form of a puzzle."""
    return "\n".join(puzzle.grid) + "\n"
