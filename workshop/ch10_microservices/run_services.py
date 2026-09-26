"""Start the four backing services (01-04) as subprocesses, and stop them on Ctrl+C.

Run: uv run python -m workshop.ch10_microservices.run_services
"""

import subprocess
import sys

SERVICES = ["01_inventory_service", "02_favorites_service", "03_cart_service", "04_product_service"]

if __name__ == "__main__":
    procs = [subprocess.Popen([sys.executable, "-m", f"{__package__}.{name}"]) for name in SERVICES]
    print(f"Started {len(procs)} services on ports 8000-8003. Ctrl+C to stop.")
    try:
        for proc in procs:
            proc.wait()
    except KeyboardInterrupt:
        for proc in procs:
            proc.terminate()
