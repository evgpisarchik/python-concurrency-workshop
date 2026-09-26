"""Listing 12.2: producer/consumer with a BOUNDED queue (back-pressure).

Use case: a producer that can outrun its consumers. Queue(5) makes
`await queue.put()` wait when the line is full, so memory stays bounded and
the producer slows down to the consumers' pace.

Run: uv run python -m workshop.ch12_queues.02_queue_producer_consumer_bounded   (stops after 15 s)
"""

import asyncio
from asyncio import Queue
from contextlib import suppress
from random import randrange

from workshop.ch12_queues.supermarket import Customer, generate_customer


async def checkout_customer(queue: Queue, cashier_number: int):
    while True:
        customer: Customer = await queue.get()  # waits for work
        print(f"Cashier {cashier_number} checking out customer {customer.customer_id}")
        for product in customer.products:
            print(f"Cashier {cashier_number} checking out customer {customer.customer_id}'s {product.name}")
            await asyncio.sleep(product.checkout_time)
        print(f"Cashier {cashier_number} finished checking out customer {customer.customer_id}")
        queue.task_done()


async def customer_generator(queue: Queue):
    customer_count = 0

    while True:
        customers = [generate_customer(i) for i in range(customer_count, customer_count + randrange(5))]
        for customer in customers:
            print("Waiting to put customer in line...")
            await queue.put(customer)  # waits while the queue is full
            print("Customer put in line!")
        customer_count = customer_count + len(customers)
        await asyncio.sleep(1)


async def main():
    customer_queue = Queue(5)

    with suppress(TimeoutError):
        async with asyncio.timeout(15):
            customer_producer = asyncio.create_task(customer_generator(customer_queue))
            cashiers = [asyncio.create_task(checkout_customer(customer_queue, i)) for i in range(3)]
            await asyncio.gather(customer_producer, *cashiers)


asyncio.run(main())
