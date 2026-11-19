#!/usr/bin/env python3
"""plot_e1.py - E1 charts and summary table from results.csv.
usage: python3 analysis/plot_e1.py data/results_e1.csv  (writes results/ and results/figures/)"""
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
TAG = src.stem.replace("results_", "")            # e1, or e1_small for the 0.5 GB database
fig_out = out / "figures" / "e1_plots"   # charts
fig_out.mkdir(parents=True, exist_ok=True)
EXP = "E1 [0.5 GB DB]" if "small" in TAG else "E1"
d = pd.read_csv(src)
d = d[d["exp"] == "E1"]

COL = {"lru_cache": "#2a78d6", "auto_hyper_clock_cache": "#eb6834"}
LBL = {"lru_cache": "LRUCache", "auto_hyper_clock_cache": "HyperClockCache (auto)"}
MRK = {"lru_cache": "o", "auto_hyper_clock_cache": "s"}
SKEW = {0.0: "Uniform (skew 0)", 10.0: "Skewed (skew 10)"}
INK, MUTED, GRID = "#1f1f1e", "#6b6b68", "#e6e6e3"

g = (d.groupby(["cache_mb", "skew", "cache"])
       .agg(ops=("ops_sec", "mean"), ops_sd=("ops_sec", "std"),
            p50=("p50_us", "mean"), p99=("p99_us", "mean"), p999=("p999_us", "mean"),
            data_miss=("data_miss_ratio", "mean"), index_miss=("index_miss_ratio", "mean"),
            filter_miss=("filter_miss_ratio", "mean"), total_miss=("total_miss_ratio", "mean"),
            cpu_us=("cpu_us_per_op", "mean"))
       .reset_index())
g.round(4).to_csv(out / f"{TAG}_summary.csv", index=False)
sizes = sorted(g["cache_mb"].unique())


def style(ax, title, ylabel):
    ax.set_title(title, loc="left", fontsize=11, color=INK, pad=8)
    ax.set_xscale("log", base=2)
    ax.set_xticks(sizes, [f"{s} MB" if s < 1024 else f"{s // 1024} GB" for s in sizes])
    ax.minorticks_off()
    ax.set_xlabel("Block cache size", color=MUTED, fontsize=9)
    ax.set_ylabel(ylabel, color=MUTED, fontsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)


def lines(ax, col, skew, err=None, pct=False):
    for c in COL:
        s = g[(g["skew"] == skew) & (g["cache"] == c)].sort_values("cache_mb")
        y = s[col] * (100 if pct else 1)
        ax.errorbar(s.cache_mb, y, yerr=None if err is None else s[err], color=COL[c],
                    marker=MRK[c], markersize=6, linewidth=2, capsize=3, label=LBL[c],
                    markeredgecolor="white", markeredgewidth=1.2)


# Figure 1: throughput
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for ax, skew in zip(axes, SKEW):
    lines(ax, "ops", skew, err="ops_sd")
    style(ax, SKEW[skew], "Throughput (ops/sec)")
    if "small" in TAG:      # fully cached points are ~50x the disk-bound ones: log axis
        ax.set_yscale("log")
        ax.set_ylabel("Throughput (ops/sec, log scale)", color=MUTED, fontsize=9)
    else:
        ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(COMMAS)
    ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
axes[0].legend(frameon=False, fontsize=9, loc="upper left")
fig.suptitle(f"{EXP} - Throughput vs. cache size (1 thread, mean of 3 runs, bars = std dev)",
             x=0.01, ha="left", fontsize=12, color=INK)
fig.tight_layout()
fig.savefig(fig_out / f"{TAG}_throughput.png", dpi=200)

# Figure 2: miss ratios (index on top, data below), one y-axis per panel
fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True)
for j, skew in enumerate(SKEW):
    lines(axes[0, j], "index_miss", skew, pct=True)
    style(axes[0, j], f"Index-block miss ratio - {SKEW[skew]}", "Miss ratio (%)")
    lines(axes[1, j], "data_miss", skew, pct=True)
    style(axes[1, j], f"Data-block miss ratio - {SKEW[skew]}", "Miss ratio (%)")
    for ax in axes[:, j]:
        ax.set_ylim(bottom=0)
axes[0, 0].legend(frameon=False, fontsize=9, loc="upper right")
fig.suptitle(f"{EXP} - Block cache miss ratio by block type", x=0.01, ha="left",
             fontsize=12, color=INK)
fig.tight_layout()
fig.savefig(fig_out / f"{TAG}_miss_ratios.png", dpi=200)
print(f"wrote {TAG}_* charts and summary to", out)
