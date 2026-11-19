#!/bin/bash
# E3 on the 0.5 GB database: shard count at 14 threads, 1 GB cache (holds all the data).
# LRU and HyperClock both at 1, 4, 16, 64 shards. Results: data/results_e3_small.csv (~1 h)
cd "$(dirname "$0")"; source small_env.sh
for SKEW in 10 0; do
  for CACHE in lru_cache auto_hyper_clock_cache; do
    for BITS in 0 2 4 6; do
      python3 bench.py --exp E3 --num $NUM --cache $CACHE --shard-bits $BITS --cache-mb 1024 \
        --hipri 0.5 --threads 14 --reads $READS_CACHED --skew $SKEW --reps 3 --results results_e3_small.csv || exit 1
    done
  done
done
echo "E3 (small) finished: $(date)"
