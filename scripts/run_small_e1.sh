#!/bin/bash
# E1 on the 0.5 GB database: cache size from ~7% of the data to twice the data.
# 1 thread, uniform and skewed keys. Results: data/results_e1_small.csv (~2.5 h)
cd "$(dirname "$0")"; source small_env.sh
declare -A HCC_BITS=([32]=0 [128]=2 [256]=3 [512]=4 [1024]=5)   # HyperClock default: 1 shard per 32 MB
for MB in 32 128 256 512 1024; do
  # cache smaller than the data: disk-bound and slow, 200,000 lookups per round
  # cache about the size of the data or bigger: fast, READS_CACHED lookups per round
  if [ $MB -lt 512 ]; then READS=200000; else READS=$READS_CACHED; fi
  for SKEW in 0 10; do
    python3 bench.py --exp E1 --num $NUM --cache lru_cache --shard-bits 6 --cache-mb $MB \
      --hipri 0.5 --threads 1 --reads $READS --skew $SKEW --reps 3 --results results_e1_small.csv || exit 1
    python3 bench.py --exp E1 --num $NUM --cache auto_hyper_clock_cache --shard-bits ${HCC_BITS[$MB]} --cache-mb $MB \
      --threads 1 --reads $READS --skew $SKEW --reps 3 --results results_e1_small.csv || exit 1
  done
done
echo "E1 (small) finished: $(date)"
