#!/bin/bash
# Step 1: install build tools and build db_bench from RocksDB 11.8.1.
# Tested on Ubuntu under WSL2.
set -e
sudo apt update
sudo apt install -y build-essential git libgflags-dev libsnappy-dev zlib1g-dev \
  libbz2-dev liblz4-dev libzstd-dev python3-pandas python3-matplotlib
cd ~
[ -d rocksdb ] || git clone --branch v11.8.1 https://github.com/facebook/rocksdb.git
cd rocksdb
DEBUG_LEVEL=0 make -j6 db_bench   # DEBUG_LEVEL=0 = release build; -j6 keeps memory use within 7 GB
./db_bench --version              
