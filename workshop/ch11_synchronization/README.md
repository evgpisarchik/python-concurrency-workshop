# Chapter 11: Synchronization: locks, semaphores, events, conditions

Run: `uv run python -m workshop.ch11_synchronization.<file>`

| File | Listing | Use case |
|---|---|---|
| `01_no_race_without_await.py` | 11.1 | Code between two `await`s is effectively atomic |
| `02_race_condition_across_await.py` | 11.2 | **Pitfall:** read → `await` → write loses updates |
| `mock_socket.py` | – | Fake socket used by 11.3 and 11.5 |
| `03_race_on_shared_connections.py` | 11.3 | **Pitfall:** a user disconnects during a broadcast |
| `04_asyncio_lock.py` | 11.4 | `asyncio.Lock`: one coroutine in the critical section at a time |
| `05_lock_protecting_shared_dict.py` | 11.5 | Fix 11.3 with a lock |
| `06_semaphore.py` | 11.6 | Limit concurrency to N |
| `07_semaphore_rate_limit_requests.py` | 11.7 | Cap concurrent HTTP calls to an API |
| `08_semaphore_extra_release_pitfall.py` | 11.8 | **Pitfall:** an extra `release()` raises the limit |
| `09_bounded_semaphore.py` | 11.9 | `BoundedSemaphore` raises on an extra release |
| `10_event.py` | 11.10 | Wake many waiters with one signal |
| `file_upload.py` + `11_event_file_upload_server.py` | 11.11, 11.12 | Upload server: "processing" waits on "received" |
| `12_event_missed_triggers.py` | 11.13 | **Pitfall:** events can drop triggers (use a queue instead) |
| `13_condition.py` | 11.14 | `Condition` = lock + notify |
| `14_condition_wait_for_state.py` | 11.15 | Wait until a state machine reaches a state |

## Key takeaways

- asyncio races happen **across `await` points**, never in the middle of plain code.
- asyncio primitives are **not thread-safe**. Use `threading` primitives for threads and
  `multiprocessing` ones for processes.
- Semaphores control *how many* run at once, Events say "it happened", and Conditions say
  "it happened AND I hold the lock". Use a Queue when every signal must be handled.
