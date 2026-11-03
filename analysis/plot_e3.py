#!/usr/bin/env python3
"""E3 charts and summary table.
usage: python plot_e3.py results_e3.csv   (writes PNGs + e3_summary.csv next to the CSV)"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

src = Path(sys.argv[1])
out = src.parent
d = pd.read_csv(src)
d = d[d["exp"] == "E3"].copy()
d["shards"] = 2 ** d["shard_bits"]
d["extra_waits"] = d["vol_cs_per_op"] - d["misses_per_op"]

g = (d.groupby(["skew", "cache", "shards"])
       .agg(runs=("ops_sec", "size"), ops=("ops_sec", "mean"), ops_sd=("ops_sec", "std"),
            p50=("p50_us", "mean"), p99=("p99_us", "mean"), p999=("p999_us", "mean"),
            data_miss=("data_miss_ratio", "mean"), cpu_us=("cpu_us_per_op", "mean"),
            disk_reads_per_op=("misses_per_op", "mean"), waits_per_op=("vol_cs_per_op", "mean"),
            extra_waits_per_op=("extra_waits", "mean"))
       .reset_index())
g.round(4).to_csv(out / "e3_summary.csv", index=False)

COL = {"lru_cache": "#2a78d6", "auto_hyper_clock_cache": "#eb6834"}
LBL = {"lru_cache": "LRUCache", "auto_hyper_clock_cache": "HyperClockCache (auto)"}
MRK = {"lru_cache": "o", "auto_hyper_clock_cache": "s"}
SKEW = {10.0: "Skewed (skew 10)", 0.0: "Uniform (skew 0)"}
INK, MUTED, GRID = "#1f1f1e", "#6b6b68", "#e6e6e3"
SHARDS = [1, 4, 16, 64]


def style(ax, title, ylabel):
    ax.set_title(title, loc="left", fontsize=11, color=INK, pad=8)
    ax.set_xscale("log", base=2)
    ax.set_xticks(SHARDS, [str(s) for s in SHARDS])
    ax.minorticks_off()
    ax.set_xlabel("Cache shards", color=MUTED, fontsize=9)
    ax.set_ylabel(ylabel, color=MUTED, fontsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.set_ylim(bottom=0)


def lines(ax, col, skew, err=None, scale=1):
    for c in COL:
        s = g[(g["skew"] == skew) & (g["cache"] == c)].sort_values("shards")
        ax.errorbar(s["shards"], s[col] * scale, yerr=None if err is None else s[err],
                    color=COL[c], marker=MRK[c], markersize=6, linewidth=2, capsize=3,
                    label=LBL[c], markeredgecolor="white", markeredgewidth=1.2)


for col, err, scale, ylabel, title, fname in [
    ("ops", "ops_sd", 1, "Throughput (ops/sec)",
     "E3 - Throughput vs. shard count (1 GB cache, 14 threads, mean of 3 runs)", "e3_throughput.png"),
    ("extra_waits_per_op", None, 100, "Extra blocking waits per 100 lookups",
     "E3 - Blocking waits not explained by disk reads (contention indicator)", "e3_extra_waits.png"),
]:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, skew in zip(axes, SKEW):
        lines(ax, col, skew, err=err, scale=scale)
        style(ax, SKEW[skew], ylabel)
    axes[0].legend(frameon=False, fontsize=9, loc="lower right" if col == "ops" else "upper right")
    fig.suptitle(title, x=0.01, ha="left", fontsize=12, color=INK)
    fig.tight_layout()
    fig.savefig(out / fname, dpi=200)

# Figure 3: data-block miss ratio
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for ax, skew in zip(axes, SKEW):
    lines(ax, "data_miss", skew, scale=100)
    style(ax, SKEW[skew], "Data-block miss ratio (%)")
    ax.set_ylim(0, 100)
    for c in COL:
        last = g[(g["skew"] == skew) & (g["cache"] == c)].sort_values("shards").iloc[-1]
        ax.annotate(f"{last['data_miss'] * 100:.1f}%", (last["shards"], last["data_miss"] * 100),
                    xytext=(6, 8 if c == "auto_hyper_clock_cache" else -14), textcoords="offset points",
                    fontsize=9, color=COL[c])
axes[0].legend(frameon=False, fontsize=9, loc="upper right")
fig.suptitle("E3 - Data-block miss ratio vs. shard count (1 GB cache, 14 threads)",
             x=0.01, ha="left", fontsize=12, color=INK)
fig.tight_layout()
fig.savefig(out / "e3_miss_ratio.png", dpi=200)
print("wrote e3_throughput.png, e3_extra_waits.png, e3_miss_ratio.png, e3_summary.csv to", out)
