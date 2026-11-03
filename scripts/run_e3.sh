#!/bin/bash
# E3: shard count at maximum threads. Cache = 1 GB, 14 threads.
# LRU with 1, 4, 16, 64 shards (shard bits 0, 2, 4, 6)
# HyperClock with 1 and 4 shards (shard bits 0, 2)
# Uniform (skew 0) and skewed (skew 10). Results go to results_e3.csv
# Run from the project folder:  bash run_e3.sh
cd "$(dirname "$0")"

T=14
TOTAL=524288                 # total lookups per phase: 2 per 4 KB block of a 1 GB cache
READS=$(( TOTAL / T ))      

for SKEW in 10 0; do
  for BITS in 0 2 4 6; do
    python3 bench.py --exp E3 --cache lru_cache --shard-bits $BITS --cache-mb 1024 --hipri 0.5 \
      --threads $T --reads $READS --skew $SKEW --reps 3 --results results_e3.csv || exit 1
  done
  for BITS in 0 2; do
    python3 bench.py --exp E3 --cache auto_hyper_clock_cache --shard-bits $BITS --cache-mb 1024 \
      --threads $T --reads $READS --skew $SKEW --reps 3 --results results_e3.csv || exit 1
  done
done
echo "E3 finished: $(date)"

