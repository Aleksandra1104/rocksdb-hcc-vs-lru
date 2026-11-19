#!/bin/bash
# E2 on the 0.5 GB database: 1-14 threads, 2 GB cache (holds all the data), 64 shards
# for both caches. Each thread does READS_CACHED lookups per round, so rounds stay
# long at every thread count. Results: data/results_e2_small.csv (~1 h)
cd "$(dirname "$0")"; source small_env.sh
for T in 1 2 4 8 14; do
  for SKEW in 0 10; do
    python3 bench.py --exp E2 --num $NUM --cache lru_cache --shard-bits 6 --cache-mb 2048 \
      --hipri 0.5 --threads $T --reads $READS_CACHED --skew $SKEW --reps 3 --results results_e2_small.csv || exit 1
    python3 bench.py --exp E2 --num $NUM --cache auto_hyper_clock_cache --shard-bits 6 --cache-mb 2048 \
      --threads $T --reads $READS_CACHED --skew $SKEW --reps 3 --results results_e2_small.csv || exit 1
  done
done
echo "E2 (small) finished: $(date)"
