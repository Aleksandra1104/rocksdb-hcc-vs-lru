#!/usr/bin/env python3
"""
bench.py - run one RocksDB block-cache configuration and record the results.

For each repeat it runs db_bench twice on a fresh copy of the database:
  A = warm-up only                 (benchmarks=readrandom)
  B = warm-up + measurement        (benchmarks=readrandom,readrandom)
Throughput and latency come from the 2nd readrandom in B (already clean).
Cache hit/miss counters and CPU time are cumulative per process, so the
measured-phase values are B minus A.

Example:
  python3 bench.py --exp smoke --cache lru_cache --shard-bits 6 \
      --cache-mb 64 --threads 1 --reads 200000 --skew 0 --reps 3
"""
import argparse, csv, os, re, shutil, subprocess, sys, time
from pathlib import Path

HOME = Path.home()
# Paths can be overridden with environment variables if your layout differs.
DB_BENCH = Path(os.environ.get("DB_BENCH", HOME / "rocksdb" / "db_bench"))
# The databases stay inside Ubuntu (fast disk). Results and logs go next to
# this script, e.g. the rocksdb_project folder on the Windows Desktop.
GOLDEN = Path(os.environ.get("LSM_GOLDEN", HOME / "lsm_golden"))
RUN_DB = Path(os.environ.get("LSM_RUN", HOME / "lsm_run"))
REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
LOG_DIR = DATA / "logs"
RESULTS = DATA / "results.csv"   # default; change per experiment with --results

# LSM settings from the setup guide (must match how lsm_golden was built)
COMMON = [
    "--use_existing_db=true", "--disable_auto_compactions=true",
    "--key_size=64", "--value_size=440",
    "--write_buffer_size=4194304", "--target_file_size_base=1048576",
    "--level0_file_num_compaction_trigger=4", "--max_bytes_for_level_multiplier=2",
    "--max_bytes_for_level_base=33554432", "--level_compaction_dynamic_level_bytes=false",
    "--num_levels=9", "--disable_wal=true", "--compression_type=none",
    "--block_size=4096", "--bloom_bits=10", "--cache_index_and_filter_blocks=true",
    "--use_direct_reads=true", "--use_direct_io_for_flush_and_compaction=true",
    "--seed=42", "--statistics=1", "--histogram=1",
]

RE_OPS = re.compile(r"readrandom\s+:\s+([\d.]+) micros/op (\d+) ops/sec")
RE_PCT = re.compile(r"Percentiles: P50: ([\d.]+) P75: ([\d.]+) P99: ([\d.]+) "
                    r"P99\.9: ([\d.]+) P99\.99: ([\d.]+)")
RE_TICK = re.compile(r"rocksdb\.block\.cache\.(data|index|filter)\.(hit|miss) COUNT : (\d+)")
KINDS = ("data", "index", "filter")

FIELDS = ["exp", "num_keys", "cache", "shard_bits", "cache_mb", "hipri", "threads", "reads_per_thread",
          "skew", "rep", "ops_sec", "p50_us", "p99_us", "p999_us",
          "data_hit", "data_miss", "index_hit", "index_miss", "filter_hit", "filter_miss",
          "data_miss_ratio", "index_miss_ratio", "filter_miss_ratio", "total_miss_ratio",
          "cpu_us_per_op", "misses_per_op", "vol_cs_per_op", "invol_cs_per_op", "timestamp"]


def fresh_db():
    """Instant fresh copy: SST files are hard links (they are never modified)."""
    if RUN_DB.exists():
        shutil.rmtree(RUN_DB)
    subprocess.run(["cp", "-al", str(GOLDEN), str(RUN_DB)], check=True)


def run_db_bench(benchmarks, a, log_path):
    """Run db_bench, save its output, return (text, rusage)."""
    cmd = [str(DB_BENCH), f"--benchmarks={benchmarks}", f"--db={RUN_DB}", *COMMON,
           f"--cache_type={a.cache}", f"--cache_numshardbits={a.shard_bits}",
           f"--cache_size={a.cache_mb * 1024 * 1024}",
           f"--cache_high_pri_pool_ratio={a.hipri}",
           f"--num={a.num}", f"--threads={a.threads}", f"--reads={a.reads}",
           f"--read_random_exp_range={a.skew}"]
    with open(log_path, "w") as f:
        f.write(" ".join(cmd) + "\n\n")
        f.flush()
        p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
        _, status, ru = os.wait4(p.pid, 0)
    if status != 0:
        sys.exit(f"db_bench failed - see {log_path}")
    return log_path.read_text(), ru


def ticks(text):
    t = {f"{k}_{h}": 0 for k in KINDS for h in ("hit", "miss")}
    for kind, hm, n in RE_TICK.findall(text):
        t[f"{kind}_{hm}"] = int(n)
    return t


def ratio(miss, hit):
    return round(miss / (miss + hit), 4) if miss + hit else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", required=True, help="experiment label, e.g. E1")
    ap.add_argument("--cache", required=True,
                    choices=["lru_cache", "auto_hyper_clock_cache", "fixed_hyper_clock_cache"])
    ap.add_argument("--shard-bits", type=int, required=True, help="shards = 2^bits")
    ap.add_argument("--cache-mb", type=int, default=64)
    ap.add_argument("--hipri", type=float, default=0.5, help="LRU high-pri pool ratio")
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--reads", type=int, default=200000, help="reads PER THREAD")
    ap.add_argument("--skew", type=float, default=0, help="read_random_exp_range")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--num", type=int, default=10_000_000,
                    help="keys in the database (must match how it was built)")
    ap.add_argument("--results", default="results.csv",
                    help="results file name, saved in data/")
    a = ap.parse_args()

    global RESULTS
    RESULTS = DATA / a.results

    if a.threads > os.cpu_count():
        sys.exit(f"threads ({a.threads}) > cores ({os.cpu_count()})")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    new_file = not RESULTS.exists()
    if not new_file:
        with open(RESULTS, newline="") as f:
            old = list(csv.DictReader(f))
        if old and list(old[0].keys()) != FIELDS:   # older file without new columns
            with open(RESULTS, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=FIELDS)
                w.writeheader()
                w.writerows({k: r.get(k, "") for k in FIELDS} for r in old)
    tag = (f"{a.exp}_{a.cache}_sb{a.shard_bits}_{a.cache_mb}MB_hp{a.hipri}"
           f"_t{a.threads}_skew{a.skew:g}")

    for rep in range(1, a.reps + 1):
        print(f"[{time.strftime('%H:%M:%S')}] {tag} rep {rep}/{a.reps}: warm-up only (A)...",
              flush=True)
        fresh_db()
        text_a, ru_a = run_db_bench("readrandom", a, LOG_DIR / f"{tag}_rep{rep}_A.log")

        print(f"[{time.strftime('%H:%M:%S')}] {tag} rep {rep}/{a.reps}: warm-up + measure (B)...",
              flush=True)
        fresh_db()
        text_b, ru_b = run_db_bench("readrandom,readrandom", a,
                                     LOG_DIR / f"{tag}_rep{rep}_B.log")

        ops = RE_OPS.findall(text_b)
        pct = RE_PCT.findall(text_b)
        if len(ops) < 2 or len(pct) < 2:
            sys.exit(f"could not find two readrandom results in rep {rep} B log")
        ops_sec = int(ops[-1][1])
        p50, _, p99, p999, _ = pct[-1]

        ta, tb = ticks(text_a), ticks(text_b)
        d = {k: tb[k] - ta[k] for k in tb}
        tot_hit = sum(d[f"{k}_hit"] for k in KINDS)
        tot_miss = sum(d[f"{k}_miss"] for k in KINDS)
        measured_ops = a.threads * a.reads

        row = dict(exp=a.exp, num_keys=a.num, cache=a.cache, shard_bits=a.shard_bits, cache_mb=a.cache_mb,
                   hipri=a.hipri, threads=a.threads, reads_per_thread=a.reads, skew=a.skew,
                   rep=rep, ops_sec=ops_sec, p50_us=p50, p99_us=p99, p999_us=p999, **d,
                   data_miss_ratio=ratio(d["data_miss"], d["data_hit"]),
                   index_miss_ratio=ratio(d["index_miss"], d["index_hit"]),
                   filter_miss_ratio=ratio(d["filter_miss"], d["filter_hit"]),
                   total_miss_ratio=ratio(tot_miss, tot_hit),
                   cpu_us_per_op=round(((ru_b.ru_utime + ru_b.ru_stime) -
                                        (ru_a.ru_utime + ru_a.ru_stime)) / measured_ops * 1e6, 2),
                   # every cache miss is one blocking disk read; voluntary context
                   # switches beyond that are threads blocking on something else,
                   # e.g. waiting for a cache shard's mutex
                   misses_per_op=round(tot_miss / measured_ops, 4),
                   vol_cs_per_op=round((ru_b.ru_nvcsw - ru_a.ru_nvcsw) / measured_ops, 4),
                   invol_cs_per_op=round((ru_b.ru_nivcsw - ru_a.ru_nivcsw) / measured_ops, 4),
                   timestamp=time.strftime("%Y-%m-%d %H:%M:%S"))
        with open(RESULTS, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            if new_file:
                w.writeheader()
                new_file = False
            w.writerow(row)
        print(f"    -> {ops_sec} ops/sec ({measured_ops / ops_sec:.1f} s measured), p99 {p99} us, total miss ratio "
              f"{row['total_miss_ratio']}, CPU {row['cpu_us_per_op']} us/op, "
              f"blocking switches {row['vol_cs_per_op']}/op", flush=True)

    shutil.rmtree(RUN_DB, ignore_errors=True)
    print(f"Done. Results appended to {RESULTS}")


if __name__ == "__main__":
    main()
