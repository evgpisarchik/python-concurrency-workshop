# Chapter 8: Streams: transports, protocols, terminal apps, chat server

Run: `uv run python -m workshop.ch08_streams.<file>`. The interactive apps (04-06, 09) need a Unix terminal.

| File | Listing | Use case |
|---|---|---|
| `http_client_protocol.py` | 8.1 | Low-level `asyncio.Protocol`, with a Future bridging callbacks back to await |
| `01_protocol_http_client.py` | 8.2 | `loop.create_connection` with a protocol |
| `02_stream_reader_http_client.py` | 8.3 | High-level streams: `open_connection` returns `(reader, writer)` |
| `03_blocking_input_pitfall.py` | 8.4 | **Pitfall:** `input()` freezes the event loop |
| `terminal.py` | 8.5, 8.7, 8.8, 8.9 | Async stdin reader, ANSI cursor control, `read_line`, `MessageStore` |
| `04_async_stdin_reader.py` | 8.6 | Read stdin without blocking |
| `05_delay_console_app.py` | 8.10 | Terminal UI: output area at the top, input line at the bottom |
| `06_async_sql_console.py` | 8.11 | Interactive tool that runs SQL queries concurrently |
| `07_echo_server_with_user_count.py` | 8.12 | `asyncio.start_server` with shared state and broadcast |
| `08_chat_server.py` | 8.13 | Chat server: a small protocol, broadcast, idle timeout |
| `09_chat_client.py` | 8.14 | Client that sends and receives at the same time |

## Key takeaways

- **Transports/protocols** are the callback-based foundation. **Streams** (`StreamReader` / `StreamWriter`) are the
  high-level, awaitable API you should normally use.
- `writer.write()` only buffers. `await writer.drain()` applies back-pressure.
- Treat stdin like any other stream (`connect_read_pipe`) so console apps don't block the loop.
