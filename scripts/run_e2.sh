#!/bin/bash
# E2: thread scaling. Cache = 2 GB, uniform (skew 0) and skewed (skew 10).
# Results go to results_e2.csv
# Run from the project folder:  bash run_e2.sh
cd "$(dirname "$0")"

TOTAL=1048576   # total lookups per phase, split across threads (fills a 2 GB cache)

for T in 1 2 4 8 14; do
  READS=$(( TOTAL / T ))         
  for SKEW in 0 10; do
    python3 bench.py --exp E2 --cache lru_cache --shard-bits 6 \
      --cache-mb 2048 --hipri 0.5 --threads $T --reads $READS --skew $SKEW --reps 3 --results results_e2.csv || exit 1
    python3 bench.py --exp E2 --cache auto_hyper_clock_cache --shard-bits 6 \
      --cache-mb 2048 --threads $T --reads $READS --skew $SKEW --reps 3 --results results_e2.csv || exit 1
  done
done
echo "E2 finished: $(date)"
