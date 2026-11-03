#!/bin/bash
# Step 2: generate the 4.8 GB test database with db_bench,
# then keep an untouched master copy that every run is copied from.
# The databases live inside Ubuntu (~), not under /mnt/c, because the Windows
# filesystem is much slower for database files.
set -e
~/rocksdb/db_bench --benchmarks=filluniquerandom,waitforcompaction,stats \
  --db=$HOME/lsm_base --num=10000000 --key_size=64 --value_size=440 \
  --write_buffer_size=4194304 --target_file_size_base=1048576 \
  --level0_file_num_compaction_trigger=4 --max_bytes_for_level_multiplier=2 \
  --max_bytes_for_level_base=33554432 --level_compaction_dynamic_level_bytes=false \
  --num_levels=9 --disable_wal=true --compression_type=none \
  --block_size=4096 --bloom_bits=10 --cache_index_and_filter_blocks=true \
  --use_direct_io_for_flush_and_compaction=true --seed=42 --threads=1 \
  2>&1 | tee "$(dirname "$0")/../data/load.log"
du -sh ~/lsm_base                 
cp -a ~/lsm_base ~/lsm_golden      # master copy; never run anything on it directly
