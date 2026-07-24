"""Figures for the report and slides, from experiments/results/results.csv.

    python experiments/plot.py
    python experiments/plot.py --csv path.csv --outdir experiments/results

Produces three PNGs (the three results slides of the presentation):

  fig1_bt_scaling.png    search effort and time vs. board size, one line
                         per backtracking variant (hard instances, medians
                         over solved runs)
  fig2_paradigms.png     solve rate within the timeout vs. board size for
                         all five solvers (hard instances)
  fig3_difficulty.png    median time per solver at one fixed size, grouped
                         by difficulty preset

Design notes: colorblind-validated palette (Okabe-Ito order), one axis
per panel, y-only grid, direct labels at line ends plus a legend.
"""

import argparse
import csv
import statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")           # write files; no window needed
import matplotlib.pyplot as plt  # noqa: E402

# CVD-validated categorical palette, fixed assignment (never re-ordered).
COLOR = {"bt": "#0072B2", "fc": "#E69F00", "full": "#009E73",
         "hc": "#D55E00", "sa": "#CC79A7"}
LABEL = {"bt": "naive BT", "fc": "BT + forward checking",
         "full": "BT + full inference", "hc": "hill climbing",
         "sa": "simulated annealing"}
BT_FAMILY = ["bt", "fc", "full"]
ALL = ["bt", "fc", "full", "hc", "sa"]


def load(csv_path):
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "size": int(r["size"]), "difficulty": r["difficulty"],
                "seed": int(r["seed"]), "solver": r["solver"],
                "solved": bool(int(r["solved"])),
                "timed_out": bool(int(r["timed_out"])),
                "nodes": int(r["nodes"]), "time_ms": float(r["time_ms"]),
                "best_cost": (None if r["best_cost"] == ""
                              else int(r["best_cost"])),
            })
    return rows


def style(ax):
    """Recessive frame: y-grid only, no top/right spines."""
    ax.grid(axis="y", color="#DDDDDD", linewidth=0.7)
    ax.set_axisbelow(True)
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)


def median_by_size(rows, solver, metric, difficulty, solved_only=True):
    """(sizes, medians) of a metric for one solver, medians over seeds."""
    per_size = {}
    for r in rows:
        if r["solver"] != solver or r["difficulty"] != difficulty:
            continue
        if solved_only and not r["solved"]:
            continue
        per_size.setdefault(r["size"], []).append(r[metric])
    sizes = sorted(per_size)
    return sizes, [statistics.median(per_size[s]) for s in sizes]


def end_label(ax, x, y, text, color):
    if x and y:
        ax.annotate(text, (x[-1], y[-1]), textcoords="offset points",
                    xytext=(6, 0), fontsize=8.5, color=color, va="center")


def fig_bt_scaling(rows, outdir, difficulty="hard"):
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.8))
    for metric, ax, ylab in [("nodes", axes[0], "search nodes (median)"),
                             ("time_ms", axes[1], "time, ms (median)")]:
        for s in BT_FAMILY:
            x, y = median_by_size(rows, s, metric, difficulty)
            y = [max(v, 0.1) for v in y]     # log axis cannot show 0
            ax.plot(x, y, marker="o", markersize=5, linewidth=2,
                    color=COLOR[s], label=LABEL[s])
            end_label(ax, x, y, s, COLOR[s])
        ax.set_yscale("log")
        ax.set_xlabel("board side (n x n)")
        ax.set_ylabel(ylab)
        style(ax)
    axes[0].legend(frameon=False, fontsize=8.5)
    fig.suptitle(f"What inference buys: backtracking variants, "
                 f"{difficulty} instances (medians over solved runs)",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(outdir / "fig1_bt_scaling.png", dpi=200)
    plt.close(fig)


def fig_paradigms(rows, outdir, difficulty="hard"):
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    for s in ALL:
        per_size = {}
        for r in rows:
            if r["solver"] == s and r["difficulty"] == difficulty:
                per_size.setdefault(r["size"], []).append(r["solved"])
        sizes = sorted(per_size)
        rate = [100 * sum(v) / len(v) for v in
                (per_size[k] for k in sizes)]
        # No end labels here: several lines end at the same value (0%)
        # and the labels would collide; the legend carries identity.
        ax.plot(sizes, rate, marker="o", markersize=5, linewidth=2,
                color=COLOR[s], label=LABEL[s])
    ax.set_xlabel("board side (n x n)")
    ax.set_ylabel("solved within timeout, %")
    ax.set_ylim(-5, 105)
    style(ax)
    ax.legend(frameon=False, fontsize=8.5, loc="lower left")
    ax.set_title(f"Complete vs. local search: solve rate, "
                 f"{difficulty} instances", fontsize=11)
    fig.tight_layout()
    fig.savefig(outdir / "fig2_paradigms.png", dpi=200)
    plt.close(fig)


def fig_difficulty(rows, outdir, size=None):
    sizes_present = sorted({r["size"] for r in rows})
    if size is None:                       # a middle size shows contrast best
        size = sizes_present[len(sizes_present) // 2]
    levels = ["easy", "medium", "hard"]
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    width = 0.15
    for i, s in enumerate(ALL):
        xs, ys = [], []
        for j, level in enumerate(levels):
            vals = [r["time_ms"] for r in rows
                    if r["solver"] == s and r["size"] == size
                    and r["difficulty"] == level and r["solved"]]
            if vals:
                xs.append(j + (i - 2) * width)
                ys.append(max(statistics.median(vals), 0.1))
        ax.bar(xs, ys, width * 0.9, color=COLOR[s], label=LABEL[s])
    ax.set_yscale("log")
    ax.set_xticks(range(len(levels)), levels)
    ax.set_xlabel("difficulty preset (wall/clue density)")
    ax.set_ylabel("time to solve, ms (median of solved runs)")
    style(ax)
    ax.legend(frameon=False, fontsize=8.5)
    ax.set_title(f"Effect of constraint density at {size}x{size} "
                 "(missing bar = no run solved)", fontsize=11)
    fig.tight_layout()
    fig.savefig(outdir / "fig3_difficulty.png", dpi=200)
    plt.close(fig)


def make_figures(csv_path, outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    rows = load(csv_path)
    fig_bt_scaling(rows, outdir)
    fig_paradigms(rows, outdir)
    fig_difficulty(rows, outdir)
    print(f"figures written to {outdir}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default="experiments/results/results.csv")
    ap.add_argument("--outdir", default="experiments/results")
    args = ap.parse_args()
    make_figures(args.csv, args.outdir)
