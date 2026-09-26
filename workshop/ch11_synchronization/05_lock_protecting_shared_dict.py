"""Listing 11.5: fix listing 11.3 with a lock.

Use case: make "broadcast to everyone" and "remove a user" mutually
exclusive. The disconnect now waits until the broadcast finishes, so no
error is raised.

Run: uv run python -m workshop.ch11_synchronization.05_lock_protecting_shared_dict
"""

import asyncio
from asyncio import Lock

from workshop.ch11_synchronization.mock_socket import make_users

user_names_to_sockets = make_users()


async def user_disconnect(username: str, user_lock: Lock):
    print(f"{username} disconnected!")
    async with user_lock:
        print(f"Removing {username} from dictionary")
        socket = user_names_to_sockets.pop(username)
        socket.close()


async def message_all_users(user_lock: Lock):
    print("Creating message tasks")
    async with user_lock:
        messages = [socket.send(f"Hello {user}") for user, socket in user_names_to_sockets.items()]
        await asyncio.gather(*messages)


async def main():
    user_lock = Lock()
    await asyncio.gather(message_all_users(user_lock), user_disconnect("Eric", user_lock))


asyncio.run(main())
