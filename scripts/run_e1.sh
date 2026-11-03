#!/bin/bash
# E1: cache size. Threads = 1, uniform (skew 0) and skewed (skew 10).
# Run from the project folder:  bash run_e1.sh
cd "$(dirname "$0")"

# Shard bits = each cache's own default for that size:
# LRU: always 64 shards
# HyperClock: one shard per 32 MB -> 32MB:0, 128MB:2, 512MB:4, 2GB:6
declare -A HCC_BITS=([32]=0 [128]=2 [512]=4 [2048]=6)

for MB in 32 128 512 2048; do
  
  READS=$(( MB * 1024 / 4 * 2 ))
  (( READS < 200000 )) && READS=200000

  for SKEW in 0 10; do
    python3 bench.py --exp E1 --cache lru_cache --shard-bits 6 \
      --cache-mb $MB --hipri 0.5 --threads 1 --reads $READS --skew $SKEW --reps 3 || exit 1
    python3 bench.py --exp E1 --cache auto_hyper_clock_cache --shard-bits ${HCC_BITS[$MB]} \
      --cache-mb $MB --threads 1 --reads $READS --skew $SKEW --reps 3 || exit 1
  done
done
echo "E1 finished: $(date)"

