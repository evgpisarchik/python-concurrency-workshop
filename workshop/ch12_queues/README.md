# Chapter 12: Queues: producer/consumer, background jobs, crawling, priorities

Run: `uv run python -m workshop.ch12_queues.<file>`

| File | Listing | Use case |
|---|---|---|
| `supermarket.py` | – | Domain objects for 12.1/12.2 |
| `01_queue_supermarket_checkout.py` | 12.1 | Split a fixed batch across N workers, then `queue.join()` |
| `02_queue_producer_consumer_bounded.py` | 12.2 | Bounded queue gives **back-pressure** on a fast producer |
| `03_web_app_order_queue.py` | 12.3 | Web endpoint responds right away while workers process later, with graceful drain on shutdown |
| `04_web_crawler.py` | 12.4 | Work that creates work: a concurrent crawler with a depth limit |
| `05_priority_queue_tuples.py` | 12.5 | `PriorityQueue` with `(priority, data)` |
| `06_priority_queue_dataclass.py` | 12.6 | Ordered dataclass where only the priority is compared |
| `07_web_app_priority_orders.py` | 12.7 | Power users' jobs jump the queue |
| `08_priority_queue_ties.py` | 12.8 | **Pitfall:** equal priorities come out in no fixed order |
| `09_priority_queue_fifo_ties.py` | 12.9 | Insertion counter as a tie-breaker gives FIFO within a priority |
| `10_lifo_queue.py` | 12.10 | `LifoQueue`: newest first (a stack) |

## Key takeaways

- `await queue.get()` / `await queue.put()` suspend when the queue is empty or full. `task_done()` + `join()` tell you when all work is finished.
- A `maxsize` bounds memory and slows producers down to the consumers' pace.
- Workers run forever, so cancel them (or on 3.13+ use `queue.shutdown()`) when you're done.
- asyncio queues are in-process only. For persistence or several machines, use Redis, RabbitMQ, SQS or Celery.
