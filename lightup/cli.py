"""Command line interface: inspect puzzles and hand-check bulb placements.

Usage examples (run from the LightUp folder):

    python -m lightup show puzzles/thesis7x7.txt
    python -m lightup check puzzles/corner2.txt --bulbs "0,1 1,0 2,2"
    python -m lightup show puzzles/thesis7x7.txt --ascii --no-color

The `check` command lets the team hand-play the game and hand-verify test
fixtures before any solver exists.  Solver commands will be added in later
steps.
"""

import argparse

from . import parser as puzzle_parser
from .render import render
from .validator import check_solution


def parse_bulbs(text):
    """Turn a string like "0,0 1,3 2,4" into the set {(0,0), (1,3), (2,4)}."""
    bulbs = set()
    for token in text.split():
        r, c = token.split(",")
        bulbs.add((int(r), int(c)))
    return bulbs


def main(argv=None):
    # Shared display flags, accepted by every subcommand.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--ascii", action="store_true",
                        help="plain ASCII output (no unicode glyphs)")
    common.add_argument("--no-color", action="store_true",
                        help="disable ANSI colors")

    ap = argparse.ArgumentParser(
        prog="lightup", description="LightUp (Akari) puzzle tools")
    sub = ap.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show", parents=[common],
                          help="render a puzzle file")
    show.add_argument("puzzle", help="path to a puzzle .txt file")

    check = sub.add_parser("check", parents=[common],
                           help="place bulbs on a puzzle and validate them")
    check.add_argument("puzzle", help="path to a puzzle .txt file")
    check.add_argument("--bulbs", default="",
                       help='bulb positions, e.g. "0,0 1,3 2,4"')

    play = sub.add_parser("play", help="play a puzzle in a window (Tkinter)")
    play.add_argument("puzzle", help="path to a puzzle .txt file")

    args = ap.parse_args(argv)

    if args.command == "play":
        # Imported here so the CLI works even on machines without Tkinter.
        from .gui import run
        run(args.puzzle)
        return 0

    puzzle = puzzle_parser.parse_file(args.puzzle)
    style = {"unicode": not args.ascii, "color": not args.no_color}

    if args.command == "show":
        print(render(puzzle, **style))

    elif args.command == "check":
        bulbs = parse_bulbs(args.bulbs)
        print(render(puzzle, bulbs, **style))
        violations = check_solution(puzzle, bulbs)
        if not violations:
            print("SOLVED - all cells lit, all clues satisfied.")
        else:
            print(f"NOT SOLVED - {len(violations)} problem(s):")
            for v in violations:
                print(f"  [{v.kind}] {v}")

    return 0
