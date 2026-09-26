"""Listing 9.6: a raw WSGI application (PEP 3333).

Use case: understand the interface under Flask/Django. It is a plain
function called once per request that returns an iterable of bytes. It is
synchronous, so a worker is tied up until the response is returned.

Run:  uv run gunicorn workshop.ch09_web_applications.06_raw_wsgi_app:application
Then: curl localhost:8000
"""


def application(env, start_response):
    start_response("200 OK", [("Content-Type", "text/html")])
    return [b"WSGI hello!"]
