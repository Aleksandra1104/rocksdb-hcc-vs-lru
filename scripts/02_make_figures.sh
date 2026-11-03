#!/bin/bash
# Step 4: rebuild every summary table and chart from the CSVs in data/.
set -e
cd "$(dirname "$0")/.."
python3 analysis/plot_e1.py data/results_e1.csv
if [ -f data/results_e2_rerun.csv ]; then
  python3 analysis/plot_e2.py data/results_e2.csv data/results_e2_rerun.csv
else
  python3 analysis/plot_e2.py data/results_e2.csv
fi
python3 analysis/plot_e3.py data/results_e3.csv
