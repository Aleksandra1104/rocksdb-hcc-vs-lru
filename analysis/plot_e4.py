#!/usr/bin/env python3
"""plot_e4.py - E4 charts and summary table (key skew at a small cache).
usage: python3 analysis/plot_e4.py data/results_e4_small.csv  (writes results/ and results/figures/)"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
COMMAS = FuncFormatter(lambda v, _: f"{v:,.0f}")   # 1,000,000 instead of 1e6

src = Path(sys.argv[1])
REPO = Path(__file__).resolve().parent.parent
out = REPO / "results"             # summary tables
TAG = src.stem.replace("results_", "")            # e4_small
fig_out = out / "figures" / "e4_plots"   # charts
fig_out.mkdir(parents=True, exist_ok=True)
EXP = "E4 [0.5 GB DB]" if "small" in TAG else "E4"

d = pd.read_csv(src)
d = d[d["exp"] == "E4"].copy()
d["extra_waits"] = d["vol_cs_per_op"] - d["misses_per_op"]
g = (d.groupby(["threads", "skew", "cache"])
       .agg(runs=("ops_sec", "size"), ops=("ops_sec", "mean"), ops_sd=("ops_sec", "std"),
            p50=("p50_us", "mean"), p99=("p99_us", "mean"), p999=("p999_us", "mean"),
            data_miss=("data_miss_ratio", "mean"), index_miss=("index_miss_ratio", "mean"),
            total_miss=("total_miss_ratio", "mean"), cpu_us=("cpu_us_per_op", "mean"),
            disk_reads_per_op=("misses_per_op", "mean"), waits_per_op=("vol_cs_per_op", "mean"),
            extra_waits_per_op=("extra_waits", "mean"))
       .reset_index())
g.round(4).to_csv(out / f"{TAG}_summary.csv", index=False)

COL = {"lru_cache": "#2a78d6", "auto_hyper_clock_cache": "#eb6834"}
LBL = {"lru_cache": "LRUCache", "auto_hyper_clock_cache": "HyperClockCache (auto)"}
MRK = {"lru_cache": "o", "auto_hyper_clock_cache": "s"}
INK, MUTED, GRID = "#1f1f1e", "#6b6b68", "#e6e6e3"
skews = sorted(g["skew"].unique())
threads = sorted(g["threads"].unique())


def style(ax, title, ylabel):
    ax.set_title(title, loc="left", fontsize=11, color=INK, pad=8)
    ax.set_xticks(skews, [f"{s:g}" + (" (uniform)" if s == 0 else "") for s in skews])
    ax.set_xlabel("Key skew (read_random_exp_range)", color=MUTED, fontsize=9)
    ax.set_ylabel(ylabel, color=MUTED, fontsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.set_ylim(bottom=0)


def lines(ax, col, t, err=None, scale=1):
    for c in COL:
        s = g[(g["threads"] == t) & (g["cache"] == c)].sort_values("skew")
        ax.errorbar(s["skew"], s[col] * scale, yerr=None if err is None else s[err],
                    color=COL[c], marker=MRK[c], markersize=6, linewidth=2, capsize=3,
                    label=LBL[c], markeredgecolor="white", markeredgewidth=1.2)


for col, err, scale, ylabel, title, fname in [
    ("ops", "ops_sd", 1, "Throughput (ops/sec)",
     f"{EXP} - Throughput vs. key skew (64 MB cache, mean of 3 runs, bars = std dev)", f"{TAG}_throughput.png"),
    ("data_miss", None, 100, "Data-block miss ratio (%)",
     f"{EXP} - Data-block miss ratio vs. key skew (64 MB cache)", f"{TAG}_miss_ratio.png"),
    ("extra_waits_per_op", None, 100, "Extra blocking waits per 100 lookups",
     f"{EXP} - Blocking waits not explained by disk reads (contention indicator)", f"{TAG}_extra_waits.png"),
]:
    fig, axes = plt.subplots(1, len(threads), figsize=(10, 4), squeeze=False)
    for ax, t in zip(axes[0], threads):
        lines(ax, col, t, err=err, scale=scale)
        style(ax, f"{t} thread" + ("s" if t > 1 else ""), ylabel)
        if col == "ops":
            ax.yaxis.set_major_formatter(COMMAS)
    axes[0][0].legend(frameon=False, fontsize=9, loc="best")
    fig.suptitle(title, x=0.01, ha="left", fontsize=12, color=INK)
    fig.tight_layout()
    fig.savefig(fig_out / fname, dpi=200)
print(f"wrote {TAG}_* charts and summary to", out)
