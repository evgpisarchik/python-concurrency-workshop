"""Injected into the stuck service by `sys.remote_exec()` in notebook 17. Runs *inside* that process."""

import asyncio

import __main__

with open("data/remote_report.txt", "w") as out:
    out.write(f"stats = {__main__.stats}\n\n")
    for task in asyncio.all_tasks():
        out.write(asyncio.format_call_graph(task) + "\n")
