# Chapter 5: Non-blocking databases with asyncpg

Prerequisite: `docker compose up -d` (see the root README), then run **in order** once:

```bash
uv run python -m workshop.ch05_async_databases.02_create_schema
uv run python -m workshop.ch05_async_databases.04_insert_random_brands
uv run python -m workshop.ch05_async_databases.05_insert_random_products_and_skus
```

| File | Listing | Use case |
|---|---|---|
| `01_connect_to_postgres.py` | 5.1 | Connect with a non-blocking driver |
| `products_db.py` | 5.2 | Schema DDL + word list loader |
| `02_create_schema.py` | 5.3 | Run DDL / migrations |
| `03_insert_and_select.py` | 5.4 | Basic CRUD, `Record` objects |
| `04_insert_random_brands.py` | 5.5 | Bulk insert with `executemany` and `$1` parameters |
| `05_insert_random_products_and_skus.py` | 5.6 | Generate a realistic dataset (1k products, 100k SKUs) |
| `06_connection_pool_queries.py` | 5.7 | Run queries concurrently through a **pool** (one connection runs one query at a time) |
| `07_pool_sequential_vs_concurrent.py` | 5.8 | Benchmark: 10k queries, sequential vs concurrent |
| `08_transaction.py` | 5.9 | `async with connection.transaction()` |
| `09_transaction_rollback.py` | 5.10 | An error rolls back the whole unit of work |
| `10_nested_transactions_savepoints.py` | 5.11 | Savepoints: an optional sub-step may fail |
| `11_manual_transaction.py` | 5.12 | Manual `start` / `commit` / `rollback` |
| `12_sync_generator.py` | 5.13 | Refresher: a regular generator |
| `13_async_generator.py` | 5.14 | Async generators and `async for` |
| `14_cursor_streaming.py` | 5.15 | Stream big result sets with a server-side cursor |
| `15_cursor_forward_fetch.py` | 5.16 | Skip rows on the server and fetch one page |
| `16_async_generator_take.py` | 5.17 | Compose async generators (`take(n)`) |

## Key takeaways

- A sync driver (psycopg2) blocks the event loop. Use asyncpg / psycopg3-async / SQLAlchemy-async.
- **One connection runs one query at a time.** For concurrency, use a pool sized to what the DB can take.
- Transactions are async context managers, and nested ones become savepoints.
- For large results, use cursors plus async generators so memory stays flat.
