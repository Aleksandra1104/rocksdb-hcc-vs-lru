#!/bin/bash
# E4 on the 0.5 GB database: key skew 0, 5, 10, 20 with a small 64 MB cache
# (about 13% of the data), at 1 and 14 threads. Default shards: LRU 64, HyperClock 2.
# Results: data/results_e4_small.csv (~1.5-2 h)
cd "$(dirname "$0")"; source small_env.sh
for T in 1 14; do
  # disk-bound: 200,000 lookups per round at 1 thread, 100,000 per thread at 14 threads
  if [ $T -eq 1 ]; then READS=200000; else READS=100000; fi
  for SKEW in 0 5 10 20; do
    python3 bench.py --exp E4 --num $NUM --cache lru_cache --shard-bits 6 --cache-mb 64 \
      --hipri 0.5 --threads $T --reads $READS --skew $SKEW --reps 3 --results results_e4_small.csv || exit 1
    python3 bench.py --exp E4 --num $NUM --cache auto_hyper_clock_cache --shard-bits 1 --cache-mb 64 \
      --threads $T --reads $READS --skew $SKEW --reps 3 --results results_e4_small.csv || exit 1
  done
done
echo "E4 (small) finished: $(date)"
