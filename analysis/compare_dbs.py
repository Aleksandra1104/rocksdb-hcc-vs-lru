#!/usr/bin/env python3
"""compare_dbs.py - puts the 4.8 GB and 0.5 GB results side by side.
usage: python3 analysis/compare_dbs.py   (reads results/e2*_summary.csv and results/e3*_summary.csv,
       so run the plot_e2.py / plot_e3.py scripts first; writes results/figures/comparison/)"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parent.parent
res = REPO / "results"
fig_out = res / "figures" / "comparison"
fig_out.mkdir(parents=True, exist_ok=True)

HCC, LRU = "auto_hyper_clock_cache", "lru_cache"
INK, MUTED, GRID, LIGHT = "#1f1f1e", "#6b6b68", "#e6e6e3", "#a3a3a0"
DBS = {"small": ("0.5 GB DB (fully cached)", INK, "o"), "": ("4.8 GB DB (disk-bound)", LIGHT, "s")}
SKEW = {10.0: ("skewed", "-"), 0.0: ("uniform", "--")}


def load(e, db):
    return pd.read_csv(res / f"{e}{'_' + db if db else ''}_summary.csv")


def style(ax, title, xlabel, ylabel, ticks):
    ax.set_title(title, loc="left", fontsize=11, color=INK, pad=8)
    ax.set_xscale("log", base=2)
    ax.set_xticks(ticks, [str(t) for t in ticks])
    ax.minorticks_off()
    ax.set_xlabel(xlabel, color=MUTED, fontsize=9)
    ax.set_ylabel(ylabel, color=MUTED, fontsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)


def draw(ax, x, y, db, skew):
    name, color, marker = DBS[db]
    ax.plot(x, y, color=color, linestyle=SKEW[skew][1], marker=marker, markersize=6, linewidth=2,
            markeredgecolor="white", markeredgewidth=1.2, label=f"{name}, {SKEW[skew][0]}")


rows = []
fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.4))

# Left: E2 - how much faster HyperClockCache is than LRUCache, per thread count
for db in DBS:
    g = load("e2", db)
    for skew in SKEW:
        s = g[g["skew"] == skew].pivot(index="threads", columns="cache", values="ops")
        lead = (s[HCC] / s[LRU] - 1) * 100
        draw(a, lead.index, lead.values, db, skew)
        rows += [dict(exp="E2", db=db or "main", skew=skew, x=t, value=round(v, 1),
                      metric="HCC lead over LRU (%)") for t, v in lead.items()]
a.axhline(0, color=MUTED, linewidth=0.8)
style(a, "E2 - HyperClockCache lead over LRUCache", "Client threads (2 GB cache, 64 shards each)",
      "HyperClockCache faster by (%)", [1, 2, 4, 8, 14])

# Right: E3 - LRUCache throughput as a share of HyperClockCache's best, per LRU shard count
for db in DBS:
    g = load("e3", db)
    for skew in SKEW:
        s = g[g["skew"] == skew]
        best = s[s["cache"] == HCC]["ops"].max()
        l = s[s["cache"] == LRU].sort_values("shards")
        pct = l["ops"] / best * 100
        draw(b, l["shards"], pct, db, skew)
        rows += [dict(exp="E3", db=db or "main", skew=skew, x=x, value=round(v, 1),
                      metric="LRU as % of HCC best") for x, v in zip(l["shards"], pct)]
b.axhline(100, color=MUTED, linewidth=0.8)
b.text(1, 101.5, "HyperClockCache (its best shard count)", fontsize=8, color=MUTED)
b.set_ylim(0, 110)
style(b, "E3 - LRUCache as % of HyperClockCache", "LRUCache shards (1 GB cache, 14 threads)",
      "LRUCache throughput (% of HyperClockCache)", [1, 4, 16, 64])

a.legend(frameon=False, fontsize=8.5, loc="upper left", handlelength=3.2)
fig.suptitle("4.8 GB vs. 0.5 GB database - once disk reads are gone, the lock cost dominates",
             x=0.01, ha="left", fontsize=12, color=INK)
fig.tight_layout()
fig.savefig(fig_out / "db_size_comparison.png", dpi=200)
pd.DataFrame(rows).to_csv(res / "comparison_summary.csv", index=False)
print("wrote comparison/db_size_comparison.png and comparison_summary.csv to", res)
