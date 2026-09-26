"""Listing 8.10: a console app with separate input and output areas.

Use case: a terminal UI (like a chat client or log viewer) where output
appears at the top while you type at the bottom. cbreak mode + ANSI escape
codes + an async stdin reader.

Run: uv run python -m workshop.ch08_streams.05_delay_console_app   (Unix, Ctrl+C to quit)
"""

import asyncio
import os
import sys
import tty

from workshop.ch08_streams.terminal import (
    MessageStore,
    create_stdin_reader,
    make_redraw,
    move_to_bottom_of_screen,
    read_line,
)


async def sleep(delay: int, message_store: MessageStore):
    await message_store.append(f"Starting delay {delay}")
    await asyncio.sleep(delay)
    await message_store.append(f"Finished delay {delay}")


async def main():
    tty.setcbreak(sys.stdin)  # read keys one by one, without waiting for Enter
    os.system("clear")
    rows = move_to_bottom_of_screen()

    messages = MessageStore(make_redraw(), rows - 1)

    stdin_reader = await create_stdin_reader()

    while True:
        line = await read_line(stdin_reader)
        delay_time = int(line)
        asyncio.create_task(sleep(delay_time, messages))


asyncio.run(main())
