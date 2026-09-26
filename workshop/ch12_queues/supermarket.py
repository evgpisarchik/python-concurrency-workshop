"""Domain objects for the supermarket checkout examples (listings 12.1, 12.2)."""

from dataclasses import dataclass
from random import randrange


@dataclass
class Product:
    name: str
    checkout_time: float


@dataclass
class Customer:
    customer_id: int
    products: list[Product]


ALL_PRODUCTS = [Product("beer", 2), Product("bananas", 0.5), Product("sausage", 0.2), Product("diapers", 0.2)]


def generate_customer(customer_id: int) -> Customer:
    products = [ALL_PRODUCTS[randrange(len(ALL_PRODUCTS))] for _ in range(randrange(10))]
    return Customer(customer_id, products)
