"""Listing 11.3: PITFALL. A user disconnects while we broadcast to them.

Use case: a realistic race in chat/websocket servers. We build the list of
send() calls, then a disconnect closes one socket before its send runs, and it
raises "Socket is closed!".

Run: uv run python -m workshop.ch11_synchronization.03_race_on_shared_connections
"""

import asyncio

from workshop.ch11_synchronization.mock_socket import make_users

user_names_to_sockets = make_users()


async def user_disconnect(username: str):
    print(f"{username} disconnected!")
    socket = user_names_to_sockets.pop(username)
    socket.close()


async def message_all_users():
    print("Creating message tasks")
    messages = [socket.send(f"Hello {user}") for user, socket in user_names_to_sockets.items()]
    await asyncio.gather(*messages)


async def main():
    await asyncio.gather(message_all_users(), user_disconnect("Eric"))


asyncio.run(main())
