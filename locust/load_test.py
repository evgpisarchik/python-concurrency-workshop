"""Run locust as 1 master + N worker processes.

A single locust process is limited by one CPU core (it's gevent-based), so to
generate heavy load, run several workers. This is multiprocessing in practice.

Run: uv run --group load python locust/load_test.py locust/work.py [workers]
UI:  http://localhost:8089
"""

import os
import subprocess
import sys
import time

LOCUSTFILE = sys.argv[1] if len(sys.argv) > 1 else "locust/work.py"
NUM_WORKERS = int(sys.argv[2]) if len(sys.argv) > 2 else max((os.cpu_count() or 2) // 2, 1)


def run_master():
    return subprocess.Popen(["locust", "-f", LOCUSTFILE, "--master"])


def run_worker():
    return subprocess.Popen(["locust", "-f", LOCUSTFILE, "--worker"])


if __name__ == "__main__":
    print(f"Running locust master with {NUM_WORKERS} workers using {LOCUSTFILE}")
    master = run_master()
    time.sleep(2)
    workers = [run_worker() for _ in range(NUM_WORKERS)]

    try:
        master.wait()
    except KeyboardInterrupt:
        print("Stopping all processes...")
        master.terminate()
        for w in workers:
            w.terminate()
