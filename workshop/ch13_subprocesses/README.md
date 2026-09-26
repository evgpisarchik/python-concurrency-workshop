# Chapter 13: Subprocesses

Run: `uv run python -m workshop.ch13_subprocesses.<file>`. 06/07 need `gpg`.

| File | Listing | Use case |
|---|---|---|
| `01_run_subprocess.py` | 13.1 | Run a CLI tool without blocking the loop |
| `02_subprocess_timeout_terminate.py` | 13.2 | Time out and terminate a hung process |
| `03_stream_subprocess_stdout.py` | 13.3 | Stream output line by line while it runs |
| `child_lots_of_output.py` | 13.4 | Child that writes ~14 MB |
| `04_pipe_deadlock_pitfall.py` | 13.5 | **Pitfall:** `wait()` + an unread PIPE leads to deadlock |
| `05_communicate.py` | 13.6 | `communicate()` reads everything safely |
| `gpg.py` + `06_concurrent_subprocesses.py` | 13.7 | Run 100 external processes concurrently |
| `07_limit_subprocesses_semaphore.py` | 13.8 | Cap them with `Semaphore(cpu_count)` |
| `child_ask_username.py` | 13.9 | Child that reads one line |
| `08_communicate_stdin.py` | 13.10 | Send input with `communicate(input)` |
| `child_echo.py` | 13.11 | Interactive echo program |
| `09_interactive_subprocess_naive.py` | 13.12 | **Pitfall:** naive read/write gets out of sync with the child |
| `child_echo_slow.py` | 13.13 | Echo with slow, random output |
| `10_interactive_subprocess_event.py` | 13.14 | Wait for the prompt (an Event), then write (like `expect`) |

## Key takeaways

- `create_subprocess_exec` (no shell) is safer than `create_subprocess_shell`.
- Always read any PIPE you open (stream it or `communicate()`), or the child can block forever.
- External processes give free parallelism for CPU-heavy tools. Limit how many run at once.
