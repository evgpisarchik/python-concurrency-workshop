"""Small helpers shared by the notebooks."""

import atexit
import os
import socket
import subprocess
import sys
import time

import marimo as mo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Set WORKSHOP_RUN_ALL=1 to run every gated demo (used to test the notebooks with `marimo export`).
RUN_ALL = os.getenv("WORKSHOP_RUN_ALL") == "1"


def gate(button, what: str = "this demo") -> None:
    """Stop the cell until its run button is clicked."""
    mo.stop(not (button.value or RUN_ALL), mo.md(f"_Click the button above to run {what}._"))


# Servers in subprocesses

_servers: dict[int, subprocess.Popen] = {}  # port -> server process


def start_server(args: list[str], port: int) -> subprocess.Popen:
    """Start `python <args>` in the background and wait until it listens on `port`.

    A server started earlier on the same port (a re-run cell) is stopped first, and every server is stopped when
    Python exits.
    """
    if port in _servers:
        stop_server(_servers.pop(port))
    proc = subprocess.Popen([sys.executable, *args], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        _wait_for_port(port)
    except TimeoutError:
        proc.kill()
        raise RuntimeError(proc.stderr.read().decode()[-2000:]) from None
    _servers[port] = proc
    return proc


def stop_server(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@atexit.register
def _stop_all_servers() -> None:
    for proc in _servers.values():
        stop_server(proc)


def _wait_for_port(port: int, timeout: float = 15) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.1)
    raise TimeoutError(f"nothing is listening on port {port} after {timeout}s")


# Other Python builds


def run_python(version: str, args: list[str], env: dict | None = None, timeout: float = 300) -> str:
    """Run `python <args>` on another Python build (e.g. "3.14t") through uv and return its stdout.

    Only the standard library and the `workshop` package are available there, and uv downloads the
    build on first use.
    """
    env = {**os.environ, "PYTHONPATH": ROOT, **(env or {})}
    env.pop("VIRTUAL_ENV", None)  # don't let uv complain about the notebook's own venv
    command = ["uv", "run", "--no-project", "--managed-python", "--python", version, "python", *args]
    result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=timeout, cwd=ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(command)} failed:\n{result.stderr[-2000:]}")
    return result.stdout
