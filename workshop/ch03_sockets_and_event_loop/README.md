# Chapter 3: Sockets: from blocking I/O to your first event loop

Run a server: `uv run python -m workshop.ch03_sockets_and_event_loop.<file>`
Connect clients with `nc 127.0.0.1 8000` (add `-C` to send `\r\n` line endings) or `telnet 127.0.0.1 8000`.

| File | Listing | Use case |
|---|---|---|
| `01_accept_connection.py` | 3.1 | Accept one TCP connection |
| `02_read_data_blocking.py` | 3.2 | Read a framed message with blocking `recv` |
| `03_blocking_multiple_clients_broken.py` | 3.3 | **Pitfall:** blocking sockets cannot serve two clients at once |
| `04_non_blocking_socket.py` | 3.4 | Switch a socket to non-blocking mode |
| `05_non_blocking_without_handling.py` | 3.5 | **Pitfall:** crashes with `BlockingIOError` |
| `06_non_blocking_busy_loop.py` | 3.6 | Multi-client server that busy-polls (100% CPU) |
| `07_selector_echo_server.py` | 3.7 | `selectors`: sleep until the OS reports a ready socket (the core of an event loop) |
| `08_asyncio_echo_server.py` | 3.8 | The same server on asyncio (one task per client, errors isolated per client) |
| `09_signal_handler.py` | 3.9 | Handle Ctrl+C / SIGTERM inside the loop |
| `10_graceful_shutdown.py` | 3.10 | Graceful shutdown: give connected clients N seconds to finish |

## Key takeaways

- A server has **one listening socket** plus **one socket per client**.
- Blocking sockets stall the whole thread. Non-blocking sockets return right away, either with data
  or with `BlockingIOError`.
- `selectors` (epoll/kqueue/IOCP) asks the OS *which* sockets are ready. Running `select()` in a loop
  and calling handlers **is** an event loop, and asyncio's `sock_recv` / `sock_accept` are built on it.
- Handle shutdown explicitly: catch the signals, stop accepting, drain in-flight work within a deadline.
- `loop.add_signal_handler` works on Unix only. On Windows, use `signal.signal()`.

```
TCP lifecycle
client ──SYN──►  server (LISTEN)
client ◄SYN+ACK─ server
client ──ACK──►  server ── accept() ─► new per-client socket (full duplex)
          ... data both ways ...
client ◄──FIN/ACK──► server   (graceful close)
```

## Try it

- Run `06`, then `07`, and compare CPU usage in `top`.
- In `08`, send `boom` from one client and check that the other clients keep working.
