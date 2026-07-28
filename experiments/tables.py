"""Emit LaTeX tables of the sweep results, for pasting into the report.

    python experiments/tables.py                 > tables.tex
    python experiments/tables.py --which solve_size

Tables produced (--which all, the default):
    solve_size    solve rate per solver x board size
    solve_diff    solve rate per solver x difficulty preset
    nodes         median search nodes per solver x size
    time          median solve time per solver x size
    fcfull        fc vs full median time, split by difficulty
    budget        5 s vs 10 s solve counts

Captions are intentionally NOT written here: write your own in the
report, and keep them below the table as the project guidelines require.
"""

import argparse
import csv
import statistics
from pathlib import Path

SOLVERS = ["bt", "fc", "full", "hc", "sa"]
NAMES = {"bt": "naive backtracking", "fc": "forward checking",
         "full": "full inference", "hc": "hill climbing",
         "sa": "simulated annealing"}
SIZES = [7, 10, 14, 18, 25]
LEVELS = ["easy", "medium", "hard"]

RESULTS = Path("experiments/results")


def load(path):
    rows = []
    for r in csv.DictReader(open(path)):
        rows.append({"size": int(r["size"]), "difficulty": r["difficulty"],
                     "solver": r["solver"], "solved": bool(int(r["solved"])),
                     "nodes": int(r["nodes"]),
                     "time_ms": float(r["time_ms"])})
    return rows


def table(header, body_rows, align, label):
    """Assemble a booktabs-free tabular (no extra packages needed)."""
    out = ["\\begin{table}[H]", "  \\centering",
           "  \\begin{tabular}{%s}" % align, "    \\hline",
           "    " + " & ".join(header) + " \\\\", "    \\hline"]
    out += ["    " + " & ".join(r) + " \\\\" for r in body_rows]
    out += ["    \\hline", "  \\end{tabular}",
            "  %% \\caption{WRITE YOUR OWN CAPTION HERE}",
            "  \\label{%s}" % label, "\\end{table}", ""]
    return "\n".join(out)


def solve_by_size(rows):
    body = []
    for s in SOLVERS:
        cells = []
        for size in SIZES:
            rs = [r for r in rows if r["solver"] == s and r["size"] == size]
            cells.append("%d/%d" % (sum(r["solved"] for r in rs), len(rs)))
        total = [r for r in rows if r["solver"] == s]
        cells.append("\\textbf{%d/%d}" % (sum(r["solved"] for r in total),
                                          len(total)))
        body.append([NAMES[s]] + cells)
    header = ["solver"] + ["$%d\\times%d$" % (n, n) for n in SIZES] + ["total"]
    return table(header, body, "l" + "c" * (len(SIZES) + 1), "tab:solvesize")


def solve_by_diff(rows):
    body = []
    for s in SOLVERS:
        cells = []
        for d in LEVELS:
            rs = [r for r in rows if r["solver"] == s and r["difficulty"] == d]
            cells.append("%d/%d" % (sum(r["solved"] for r in rs), len(rs)))
        body.append([NAMES[s]] + cells)
    return table(["solver"] + LEVELS, body, "l" + "c" * len(LEVELS),
                 "tab:solvediff")


def metric_by_size(rows, metric, label, fmt="%.0f"):
    body = []
    for s in SOLVERS:
        cells = []
        for size in SIZES:
            vals = [r[metric] for r in rows
                    if r["solver"] == s and r["size"] == size and r["solved"]]
            cells.append(fmt % statistics.median(vals) if vals else "---")
        body.append([NAMES[s]] + cells)
    header = ["solver"] + ["$%d\\times%d$" % (n, n) for n in SIZES]
    return table(header, body, "l" + "c" * len(SIZES), label)


def fc_vs_full(rows):
    body = []
    for d in LEVELS:
        for s in ["fc", "full"]:
            cells = []
            for size in SIZES:
                vals = [r["time_ms"] for r in rows
                        if r["solver"] == s and r["size"] == size
                        and r["difficulty"] == d and r["solved"]]
                cells.append("%.2f" % statistics.median(vals) if vals else "---")
            body.append([d if s == "fc" else "", NAMES[s]] + cells)
    header = ["preset", "solver"] + ["$%d\\times%d$" % (n, n) for n in SIZES]
    return table(header, body, "ll" + "c" * len(SIZES), "tab:fcfull")


def budget(rows5, rows10):
    body = []
    for s in SOLVERS:
        a = sum(r["solved"] for r in rows5 if r["solver"] == s)
        b = sum(r["solved"] for r in rows10 if r["solver"] == s)
        body.append([NAMES[s], "%d/75" % a, "%d/75" % b, "%+d" % (b - a)])
    return table(["solver", "5\\,s budget", "10\\,s budget", "$\\Delta$"],
                 body, "lccc", "tab:budget")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--which", default="all")
    ap.add_argument("--csv", default=str(RESULTS / "results.csv"))
    ap.add_argument("--csv10", default=str(RESULTS / "results_10s.csv"))
    args = ap.parse_args()

    rows = load(args.csv)
    wanted = args.which
    parts = []
    if wanted in ("all", "solve_size"):
        parts.append(solve_by_size(rows))
    if wanted in ("all", "solve_diff"):
        parts.append(solve_by_diff(rows))
    if wanted in ("all", "nodes"):
        parts.append(metric_by_size(rows, "nodes", "tab:nodes"))
    if wanted in ("all", "time"):
        parts.append(metric_by_size(rows, "time_ms", "tab:time", "%.1f"))
    if wanted in ("all", "fcfull"):
        parts.append(fc_vs_full(rows))
    if wanted in ("all", "budget"):
        parts.append(budget(rows, load(args.csv10)))
    print("\n".join(parts))


if __name__ == "__main__":
    main()
