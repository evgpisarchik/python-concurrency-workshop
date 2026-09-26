"""Book section 9.4: Django async views, sync_to_async and async_to_sync.

A single-file Django project (the book's async_views project, condensed).

Use cases:
  /requests/?url=https://example.com&request_num=10
        an ASYNC view fans out N HTTP calls with aiohttp + gather(return_exceptions=True)
  /requests/sync_to_async?sleep_time=1&num_calls=5&thread_sensitive=False
        call BLOCKING code from an async view. thread_sensitive=True runs every call
        on one shared thread (serial, ~5 s); False uses a thread pool (~1 s)
  /requests/async_to_sync?url=https://example.com&request_num=10
        call ASYNC code from a SYNC view (useful under WSGI)

Run (ASGI): uv run uvicorn workshop.ch09_web_applications.10_django_async_views:app
Run (WSGI): uv run gunicorn workshop.ch09_web_applications.10_django_async_views:wsgi_app
"""

import asyncio
import time
from datetime import datetime
from functools import partial

import aiohttp
import django
from aiohttp import ClientSession
from django.conf import settings

settings.configure(
    DEBUG=True,
    SECRET_KEY="workshop-not-secret",
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["*"],
    TEMPLATES=[{"BACKEND": "django.template.backends.django.DjangoTemplates"}],
)
django.setup()

from asgiref.sync import async_to_sync, sync_to_async  # noqa: E402
from django.core.asgi import get_asgi_application  # noqa: E402
from django.core.wsgi import get_wsgi_application  # noqa: E402
from django.http import HttpResponse  # noqa: E402
from django.template import engines  # noqa: E402
from django.urls import path  # noqa: E402

REQUESTS_TEMPLATE = engines["django"].from_string(
    """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Request Summary</title></head>
<body>
<h1>Summary of requests:</h1>
<h2>Failures:</h2>
<table>{% for failure in failed_results %}<tr><td>{{ failure }}</td></tr>{% endfor %}</table>
<h2>Successful Results:</h2>
<table>
  <tr><td>Status code</td><td>Response time (microseconds)</td><td>Response size</td></tr>
  {% for result in successful_results %}
  <tr><td>{{ result.status }}</td><td>{{ result.time }}</td><td>{{ result.body_length }}</td></tr>
  {% endfor %}
</table>
</body></html>"""
)


async def get_url_details(session: ClientSession, url: str):
    start_time = datetime.now()
    async with session.get(url) as response:
        response_body = await response.text()
    end_time = datetime.now()
    return {
        "status": response.status,
        "time": (end_time - start_time).microseconds,
        "body_length": len(response_body),
    }


async def make_requests(url: str, request_num: int):
    async with aiohttp.ClientSession() as session:
        requests = [get_url_details(session, url) for _ in range(request_num)]
        results = await asyncio.gather(*requests, return_exceptions=True)
        failed_results = [str(result) for result in results if isinstance(result, Exception)]
        successful_results = [result for result in results if not isinstance(result, Exception)]
        return {"failed_results": failed_results, "successful_results": successful_results}


async def requests_view(request):
    url: str = request.GET.get("url", "https://www.example.com")
    request_num: int = int(request.GET.get("request_num", 10))
    context = await make_requests(url, request_num)
    return HttpResponse(REQUESTS_TEMPLATE.render(context))


def sleep(seconds: int):
    time.sleep(seconds)


async def sync_to_async_view(request):
    sleep_time: int = int(request.GET.get("sleep_time", 1))
    num_calls: int = int(request.GET.get("num_calls", 5))
    thread_sensitive: bool = request.GET.get("thread_sensitive", "False") == "True"
    function = sync_to_async(partial(sleep, sleep_time), thread_sensitive=thread_sensitive)
    start = time.perf_counter()
    await asyncio.gather(*[function() for _ in range(num_calls)])
    return HttpResponse(f"{num_calls} x sleep({sleep_time}) took {time.perf_counter() - start:.2f} s\n")


def requests_view_sync(request):
    url: str = request.GET.get("url", "https://www.example.com")
    request_num: int = int(request.GET.get("request_num", 10))
    context = async_to_sync(partial(make_requests, url, request_num))()
    return HttpResponse(REQUESTS_TEMPLATE.render(context))


urlpatterns = [
    path("requests/", requests_view, name="requests"),
    path("requests/sync_to_async", sync_to_async_view),
    path("requests/async_to_sync", requests_view_sync),
]

app = get_asgi_application()
wsgi_app = get_wsgi_application()
