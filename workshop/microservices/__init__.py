"""Four small aiohttp services plus a backend-for-frontend (BFF) that aggregates them.

Each is started by the notebook as:  python -m workshop.microservices.<name>
"""

PRODUCT_PORT = 8201
INVENTORY_PORT = 8202
FAVORITES_PORT = 8203
CART_PORT = 8204
BFF_PORT = 8200
