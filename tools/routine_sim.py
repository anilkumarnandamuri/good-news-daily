#!/usr/bin/env python3
"""Simulate the twice-daily routine on a throwaway copy of HEAD and fail on any summary regression.

The routine runs in the main checkout:  git pull --ff-only origin main;  python scripts/build.py;
commit data/news.json;  push.  It keeps data/summaries.json as a local, uncommitted cache.

This script: git archive HEAD -> temp dir; optionally overlays a read-only copy of the routine's
local cache (--local-cache); runs `python3 scripts/build.py` there with every GOOD_NEWS_LLM* variable
removed (needs network: RSS + the free translation endpoints); then compares stories that have both
EN and TE summaries against the baseline data/news.json at --baseline-ref (default origin/main).
Exit 0 = no regression. Never writes to the repo.
"""
import argparse, json, os, pathlib, subprocess, sys, tempfile, time

def summarized(items):
    return sum(1 for i in items if isinstance(i.get("sum_en"), str) and i["sum_en"].strip()
               and isinstance(i.get("sum_te"), str) and i["sum_te"].strip()
               and i.get("summary_status", "paired") != "excerpt")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(pathlib.Path(__file__).resolve().parents[1]))
    ap.add_argument("--baseline-ref", default="origin/main")
    ap.add_argument("--local-cache", default=None, help="read-only copy source for data/summaries.json (the routine's local cache)")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    base = json.loads(subprocess.check_output(["git", "-C", a.repo, "show", f"{a.baseline_ref}:data/news.json"]))
    b_total, b_sum = len(base["items"]), summarized(base["items"])
    tmp = tempfile.mkdtemp(prefix="gn-routine-sim-")
    arch = subprocess.run(["git", "-C", a.repo, "archive", "HEAD"], check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", tmp], input=arch, check=True)
    if a.local_cache:
        (pathlib.Path(tmp) / "data/summaries.json").write_bytes(pathlib.Path(a.local_cache).read_bytes())
    env = {k: v for k, v in os.environ.items() if not k.startswith("GOOD_NEWS_LLM")}
    t0 = time.time()
    r = subprocess.run([sys.executable, "scripts/build.py"], cwd=tmp, env=env, capture_output=True, text=True, timeout=a.timeout)
    secs = round(time.time() - t0)
    tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-6:])
    if r.returncode != 0:
        print(f"ROUTINE-SIM: FAIL build.py exit {r.returncode} after {secs}s\n{tail}"); return 1
    new = json.loads((pathlib.Path(tmp) / "data/news.json").read_text())
    n_total, n_sum = len(new["items"]), summarized(new["items"])
    from collections import Counter
    st = dict(Counter(i.get("summary_status", "<none>") for i in new["items"]))
    print(f"baseline {a.baseline_ref}: {b_sum}/{b_total} stories with EN+TE summaries")
    print(f"simulated routine (no LLM env, {secs}s): {n_sum}/{n_total} stories with EN+TE summaries; summary_status={st}")
    for line in (r.stdout + r.stderr).splitlines():
        if line.startswith("summaries:"): print(line)
    ok = n_sum >= b_sum or n_sum == n_total
    print("ROUTINE-SIM:", "PASS" if ok else "FAIL (regression to excerpt-only)", f"(temp copy: {tmp})" if a.keep else "")
    if not a.keep: subprocess.run(["rm", "-rf", tmp])
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
