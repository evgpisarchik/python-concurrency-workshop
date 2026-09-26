"""A fake socket used by listings 11.3 and 11.5."""

import asyncio


class MockSocket:
    def __init__(self):
        self.socket_closed = False

    async def send(self, msg: str):
        if self.socket_closed:
            raise Exception("Socket is closed!")
        print(f"Sending: {msg}")
        await asyncio.sleep(1)
        print(f"Sent: {msg}")

    def close(self):
        self.socket_closed = True


def make_users() -> dict[str, MockSocket]:
    return {"John": MockSocket(), "Terry": MockSocket(), "Graham": MockSocket(), "Eric": MockSocket()}
