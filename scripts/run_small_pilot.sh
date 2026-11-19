#!/bin/bash
# Pilot (~5 min): one LRU run at 1 and at 14 threads on the small database, 2 GB cache.
# Check two things in the printed lines:
#   1. "total miss ratio" close to 0  -> the database really fits in the cache
#   2. "(X s measured)" at least ~5 s -> rounds are long enough to be stable
cd "$(dirname "$0")"; source small_env.sh
for T in 1 14; do
  python3 bench.py --exp PILOT --num $NUM --cache lru_cache --shard-bits 6 --cache-mb 2048 \
    --hipri 0.5 --threads $T --reads $READS_CACHED --skew 0 --reps 1 \
    --results results_pilot_small.csv || exit 1
done
