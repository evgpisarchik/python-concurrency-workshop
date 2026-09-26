"""Listing 9.5: the same /brands endpoint in Flask (sync, WSGI), for comparison.

Use case: compare a classic sync stack with the async one. Concurrency comes
from gunicorn worker processes/threads, not from an event loop. Load-test
both versions (see locust/brands.py) and compare requests per second.

Run: uv run gunicorn -w 8 -b 127.0.0.1:8000 workshop.ch09_web_applications.05_flask_brands_wsgi:app
     (the book compares this against 08_starlette_brands with 8 uvicorn workers)
"""

import psycopg
from flask import Flask, jsonify

from workshop.common import dsn

app = Flask(__name__)

db = psycopg.connect(dsn("products"))  # one blocking connection per worker process


@app.route("/brands")
def brands():
    with db.cursor() as cur:
        cur.execute("SELECT brand_id, brand_name FROM brand")
        rows = cur.fetchall()
    return jsonify([{"brand_id": row[0], "brand_name": row[1]} for row in rows])
