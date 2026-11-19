#!/bin/bash
# Fully cached rerun, step 1: generate a 0.5 GB database (1 million keys instead
# of 10 million; everything else identical to 01_build_database.sh). About 1 minute.
# It gets its own folders, so the 4.8 GB database (~/lsm_golden) is untouched.
set -e
~/rocksdb/db_bench --benchmarks=filluniquerandom,waitforcompaction,stats \
  --db=$HOME/lsm_small_base --num=1000000 --key_size=64 --value_size=440 \
  --write_buffer_size=4194304 --target_file_size_base=1048576 \
  --level0_file_num_compaction_trigger=4 --max_bytes_for_level_multiplier=2 \
  --max_bytes_for_level_base=33554432 --level_compaction_dynamic_level_bytes=false \
  --num_levels=9 --disable_wal=true --compression_type=none \
  --block_size=4096 --bloom_bits=10 --cache_index_and_filter_blocks=true \
  --use_direct_io_for_flush_and_compaction=true --seed=42 --threads=1 \
  2>&1 | tee "$(dirname "$0")/../data/load_small.log"
du -sh ~/lsm_small_base                          # expect: about 0.5G
rm -rf ~/lsm_small_golden
cp -a ~/lsm_small_base ~/lsm_small_golden        # master copy for every small run
