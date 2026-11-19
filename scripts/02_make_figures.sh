#!/bin/bash
# Rebuild every summary table and chart from the CSVs in data/.
# Charts are named after their data file: e1_*, e1_small_*, and so on.
set -e
cd "$(dirname "$0")/.."
for E in e1 e2 e3 e4; do
  for F in data/results_${E}.csv data/results_${E}_small.csv; do
    [ -f "$F" ] || continue
    if [ "$F" = data/results_e2.csv ] && [ -f data/results_e2_rerun.csv ]; then
      python3 analysis/plot_e2.py "$F" data/results_e2_rerun.csv
    else
      python3 analysis/plot_${E}.py "$F"
    fi
  done
done
# 4.8 GB vs 0.5 GB side by side (needs both E2 and E3 summaries)
if [ -f results/e2_small_summary.csv ] && [ -f results/e3_small_summary.csv ] \
   && [ -f results/e2_summary.csv ] && [ -f results/e3_summary.csv ]; then
  python3 analysis/compare_dbs.py
fi
