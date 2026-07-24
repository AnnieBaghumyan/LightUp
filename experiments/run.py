"""Experiment harness: sweep all solvers over generated instances.

For every (size, difficulty, seed) an instance is generated once and given
to every solver — the comparison is always on identical puzzles.  Local
search additionally uses the instance seed as its own random seed, so the
whole sweep is reproducible.

Usage (from the LightUp folder, venv active):

    python experiments/run.py                 # full sweep  (takes a while)
    python experiments/run.py --quick         # tiny sanity sweep
    python experiments/run.py --sizes 7 10 --seeds 3 --timeout 5

Writes one CSV row per run to experiments/results/results.csv
(override with --out).  Plots are made separately by experiments/plot.py.
"""

import argparse
import csv
import sys
import time
from pathlib import Path

# Allow running as a plain script: put the repo root on the path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lightup.generator import DIFFICULTY, generate               # noqa: E402
from lightup.solvers import (solve_annealing, solve_forward,      # noqa: E402
                             solve_full, solve_hillclimb,
                             solve_naive)

SOLVERS = {
    "bt": solve_naive,
    "fc": solve_forward,
    "full": solve_full,
    "hc": solve_hillclimb,
    "sa": solve_annealing,
}
LOCAL = {"hc", "sa"}          # randomized solvers that take a seed

FIELDS = ["size", "difficulty", "seed", "solver", "solved", "timed_out",
          "nodes", "conflicts", "backtracks", "propagations", "time_ms",
          "best_cost"]


def run_sweep(sizes, difficulties, seeds, timeout_s, out_csv):
    """Run the full grid and write one CSV row per (instance, solver)."""
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    total = len(sizes) * len(difficulties) * seeds * len(SOLVERS)
    done = 0
    started = time.perf_counter()

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for size in sizes:
            for level in difficulties:
                for seed in range(seeds):
                    puzzle, _ = generate(size, size, seed=seed,
                                         **DIFFICULTY[level])
                    for name, solver in SOLVERS.items():
                        if name in LOCAL:
                            result = solver(puzzle, timeout_s=timeout_s,
                                            seed=seed)
                        else:
                            result = solver(puzzle, timeout_s=timeout_s)
                        s = result.stats
                        writer.writerow({
                            "size": size, "difficulty": level, "seed": seed,
                            "solver": name,
                            "solved": int(result.solved),
                            "timed_out": int(result.timed_out),
                            "nodes": s.nodes, "conflicts": s.conflicts,
                            "backtracks": s.backtracks,
                            "propagations": s.propagations,
                            "time_ms": round(s.time_ms, 2),
                            "best_cost": ("" if result.best_cost is None
                                          else result.best_cost),
                        })
                        f.flush()   # a killed run still leaves usable data
                        done += 1
                        outcome = ("solved" if result.solved else
                                   "TIMEOUT" if result.timed_out else
                                   "no-solution")
                        print(f"[{done}/{total}] {size}x{size} {level:6s} "
                              f"seed{seed} {name:4s} {outcome:11s} "
                              f"{s.time_ms:8.0f}ms", flush=True)

    minutes = (time.perf_counter() - started) / 60
    print(f"done: {total} runs in {minutes:.1f} min -> {out_csv}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sizes", type=int, nargs="+",
                    default=[7, 10, 14, 18, 25])
    ap.add_argument("--difficulties", nargs="+",
                    default=["easy", "medium", "hard"],
                    choices=list(DIFFICULTY))
    ap.add_argument("--seeds", type=int, default=5,
                    help="instances per (size, difficulty) bucket")
    ap.add_argument("--timeout", type=float, default=5.0,
                    help="per-run budget in seconds")
    ap.add_argument("--out", default="experiments/results/results.csv")
    ap.add_argument("--quick", action="store_true",
                    help="tiny sweep for a quick sanity check")
    args = ap.parse_args()

    if args.quick:
        args.sizes, args.seeds, args.timeout = [5, 7], 2, 2.0

    run_sweep(args.sizes, args.difficulties, args.seeds, args.timeout,
              args.out)


if __name__ == "__main__":
    main()
