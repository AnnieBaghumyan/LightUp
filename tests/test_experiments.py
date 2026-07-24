"""End-to-end test of the experiment harness: a micro sweep through the
real CLI scripts, then figure generation from the resulting CSV."""

import csv
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_micro_sweep_and_figures(tmp_path):
    out_csv = tmp_path / "results.csv"
    run = subprocess.run(
        [sys.executable, "experiments/run.py", "--sizes", "5",
         "--difficulties", "easy", "--seeds", "1", "--timeout", "3",
         "--out", str(out_csv)],
        cwd=REPO, capture_output=True, text=True, timeout=120)
    assert run.returncode == 0, run.stderr
    with open(out_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 5                      # one row per solver
    assert {r["solver"] for r in rows} == {"bt", "fc", "full", "hc", "sa"}
    # 5x5 easy must be solved by every solver well within 3 seconds.
    assert all(r["solved"] == "1" for r in rows), rows

    plot = subprocess.run(
        [sys.executable, "experiments/plot.py", "--csv", str(out_csv),
         "--outdir", str(tmp_path)],
        cwd=REPO, capture_output=True, text=True, timeout=120)
    assert plot.returncode == 0, plot.stderr
    for name in ["fig1_bt_scaling.png", "fig2_paradigms.png",
                 "fig3_difficulty.png"]:
        assert (tmp_path / name).exists(), name