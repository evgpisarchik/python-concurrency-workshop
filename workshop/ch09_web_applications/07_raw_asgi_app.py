"""Listing 9.7: a raw ASGI application.

Use case: understand the interface under Starlette/FastAPI/Django-async. It is a
coroutine that receives a `scope` and exchanges events with the server through
`receive`/`send`. Because it is async, one worker can handle many requests,
WebSockets and streaming.

Run:  uv run uvicorn workshop.ch09_web_applications.07_raw_asgi_app:application
Then: curl localhost:8000
"""


async def application(scope, receive, send):
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"text/html"]],
        }
    )
    await send({"type": "http.response.body", "body": b"ASGI hello!"})
