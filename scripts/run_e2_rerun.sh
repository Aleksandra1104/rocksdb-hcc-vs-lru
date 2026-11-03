#!/bin/bash
# Reruns the two E2 configurations disturbed by other activity on my laptop.
# Results go to data/results_e2_rerun.csv.
# Run:  bash scripts/run_e2_rerun.sh
cd "$(dirname "$0")"
python3 bench.py --exp E2 --cache lru_cache --shard-bits 6 --cache-mb 2048 --hipri 0.5 \
  --threads 1 --reads 1048576 --skew 0 --reps 3 --results results_e2_rerun.csv || exit 1
python3 bench.py --exp E2 --cache lru_cache --shard-bits 6 --cache-mb 2048 --hipri 0.5 \
  --threads 4 --reads 262144 --skew 0 --reps 3 --results results_e2_rerun.csv || exit 1
echo "Rerun finished: $(date)"
