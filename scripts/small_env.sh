# Settings shared by all small-database runs (sourced by run_small_*.sh).
export LSM_GOLDEN=$HOME/lsm_small_golden   # master copy of the 0.5 GB database
export LSM_RUN=$HOME/lsm_small_run         # fresh copy made for each execution
NUM=1000000                                # keys in the small database
# Lookups per thread in each round when the cache holds the whole database.
# Fully cached lookups are fast, so this keeps each measured round several
# seconds long; raise it if the pilot shows rounds shorter than ~5 s.
READS_CACHED=${READS_CACHED:-1000000}
[ -d "$LSM_GOLDEN" ] || { echo "Missing $LSM_GOLDEN - run scripts/03_build_small_database.sh first"; exit 1; }
