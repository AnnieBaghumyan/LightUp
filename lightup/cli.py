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

    solve = sub.add_parser("solve", parents=[common],
                           help="solve a puzzle with an AI solver")
    solve.add_argument("puzzle", help="path to a puzzle .txt file")
    solve.add_argument("--solver", choices=["bt"], default="bt",
                       help="bt = naive backtracking baseline (default)")
    solve.add_argument("--max-solutions", type=int, default=1, metavar="N",
                       help="stop after N solutions (2 = uniqueness check)")
    solve.add_argument("--timeout", type=float, default=None, metavar="SEC",
                       help="give up after this many seconds")
    solve.add_argument("--log", action="store_true",
                       help="print every solver decision")
    solve.add_argument("--step", action="store_true",
                       help="pause after every decision; Enter advances")

    gen = sub.add_parser("generate", parents=[common],
                         help="generate a random solvable puzzle")
    gen.add_argument("size", help='board size (3-25 per side), e.g. "7x7"')
    gen.add_argument("--difficulty", choices=["easy", "medium", "hard"],
                     help="preset for wall/clue density")
    gen.add_argument("--walls", type=float, default=None,
                     help="fraction of cells that become walls "
                          "(overrides --difficulty)")
    gen.add_argument("--clues", type=float, default=None,
                     help="fraction of walls that get a number "
                          "(overrides --difficulty)")
    gen.add_argument("--no-symmetry", action="store_true",
                     help="disable 180-degree rotational symmetry of walls")
    gen.add_argument("--seed", type=int, default=None,
                     help="random seed for a reproducible puzzle")
    gen.add_argument("--out", metavar="FILE",
                     help="also save the puzzle to this file")
    gen.add_argument("--play", action="store_true",
                     help="open the generated puzzle in the game window")
    gen.add_argument("--show-solution", action="store_true",
                     help="print the bulb placement the puzzle was built from")

    args = ap.parse_args(argv)

    if args.command == "play":
        # Imported here so the CLI works even on machines without Tkinter.
        from .gui import run
        run(args.puzzle)
        return 0

    if args.command == "generate":
        from .generator import DIFFICULTY, MAX_SIZE, MIN_SIZE, generate
        try:
            width, height = (int(n) for n in args.size.lower().split("x"))
        except ValueError:
            ap.error(f'size must look like "7x7", got {args.size!r}')
        if not (MIN_SIZE <= width <= MAX_SIZE
                and MIN_SIZE <= height <= MAX_SIZE):
            ap.error(f"each side must be {MIN_SIZE}-{MAX_SIZE}, "
                     f"got {width}x{height}")

        # Explicit --walls/--clues win over the --difficulty preset,
        # which wins over the plain defaults.
        preset = DIFFICULTY[args.difficulty] if args.difficulty else {}
        walls = args.walls if args.walls is not None \
            else preset.get("wall_density", 0.18)
        clues = args.clues if args.clues is not None \
            else preset.get("clue_density", 0.85)

        puzzle, solution = generate(
            height, width, wall_density=walls, clue_density=clues,
            symmetric=not args.no_symmetry, seed=args.seed)

        style = {"unicode": not args.ascii, "color": not args.no_color}
        print(render(puzzle, **style))
        if args.show_solution:
            print("solution bulbs:",
                  " ".join(f"{r},{c}" for r, c in sorted(solution)))
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(puzzle_parser.to_text(puzzle))
            print(f"saved to {args.out}")
        if args.play:
            from .gui import run_puzzle
            run_puzzle(puzzle, title=f"generated {args.size}"
                                     + (f" (seed {args.seed})"
                                        if args.seed is not None else ""))
        return 0

    puzzle = puzzle_parser.parse_file(args.puzzle)
    style = {"unicode": not args.ascii, "color": not args.no_color}

    if args.command == "show":
        print(render(puzzle, **style))

    elif args.command == "solve":
        from .backtracking import solve as bt_solve

        observer = None
        if args.log or args.step:
            def observer(event, cell, bulbs):
                print(f"[{event}] {cell if cell is not None else ''}")
                if args.step:
                    print(render(puzzle, bulbs, **style))
                    input("-- Enter = next step, Ctrl+C = abort --")

        result = bt_solve(puzzle, observer=observer,
                          max_solutions=args.max_solutions,
                          timeout_s=args.timeout)

        print(render(puzzle, result.bulbs, **style))
        if result.solved:
            found = len(result.solutions)
            note = ""
            if args.max_solutions >= 2 and not result.timed_out:
                note = ("  (unique)" if found == 1
                        else f"  (multiple solutions exist)")
            print(f"SOLVED - {found} solution(s) found{note}")
        elif result.timed_out:
            print(f"TIMED OUT after {args.timeout}s - no solution found yet")
        else:
            print("NO SOLUTION - the search space is exhausted.")
        s = result.stats
        print(f"stats: nodes={s.nodes}  conflicts={s.conflicts}  "
              f"backtracks={s.backtracks}  time={s.time_ms:.1f}ms")

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
