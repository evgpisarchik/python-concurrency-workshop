"""Listing 12.1: a fixed line of customers served by 3 cashiers (workers).

Use case: split a fixed batch of jobs across N worker tasks. queue.join()
waits until every item has been marked with task_done().

Run: uv run python -m workshop.ch12_queues.01_queue_supermarket_checkout
"""

import asyncio
from asyncio import Queue

from workshop.ch12_queues.supermarket import Customer, generate_customer


async def checkout_customer(queue: Queue, cashier_number: int):
    while not queue.empty():  # fine here: nothing is added after start-up
        customer: Customer = queue.get_nowait()
        print(f"Cashier {cashier_number} checking out customer {customer.customer_id}")
        for product in customer.products:
            print(f"Cashier {cashier_number} checking out customer {customer.customer_id}'s {product.name}")
            await asyncio.sleep(product.checkout_time)
        print(f"Cashier {cashier_number} finished checking out customer {customer.customer_id}")
        queue.task_done()


async def main():
    customer_queue = Queue()

    for i in range(10):
        customer_queue.put_nowait(generate_customer(i))

    cashiers = [asyncio.create_task(checkout_customer(customer_queue, i)) for i in range(3)]

    await asyncio.gather(customer_queue.join(), *cashiers)


asyncio.run(main())
