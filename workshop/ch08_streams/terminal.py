"""Terminal helpers for the interactive console apps in chapter 8.

Listing 8.5: create_stdin_reader - wrap stdin in an asyncio StreamReader
Listing 8.7: ANSI escape codes to move the cursor and clear lines
Listing 8.8: read_line - read one char at a time, echo it and handle backspace
Listing 8.9: MessageStore - a bounded deque that redraws the screen on change

Unix only (uses tty and connect_read_pipe on stdin).
"""

import asyncio
import shutil
import sys
from asyncio import StreamReader
from collections import deque
from collections.abc import Awaitable, Callable


# --- Listing 8.5 -----------------------------------------------------------
async def create_stdin_reader() -> StreamReader:
    stream_reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(stream_reader)
    loop = asyncio.get_running_loop()
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    return stream_reader


# --- Listing 8.7 -----------------------------------------------------------
def save_cursor_position():
    sys.stdout.write("\0337")


def restore_cursor_position():
    sys.stdout.write("\0338")


def move_to_top_of_screen():
    sys.stdout.write("\033[H")


def delete_line():
    sys.stdout.write("\033[2K")


def clear_line():
    sys.stdout.write("\033[2K\033[0G")


def move_back_one_char():
    sys.stdout.write("\033[1D")


def move_to_bottom_of_screen() -> int:
    _, total_rows = shutil.get_terminal_size()
    input_row = total_rows - 1
    sys.stdout.write(f"\033[{input_row}E")
    return total_rows


# --- Listing 8.8 -----------------------------------------------------------
async def read_line(stdin_reader: StreamReader) -> str:
    def erase_last_char():
        move_back_one_char()
        sys.stdout.write(" ")
        move_back_one_char()

    delete_char = b"\x7f"
    input_buffer = deque()
    while (input_char := await stdin_reader.read(1)) != b"\n":
        if input_char == delete_char:
            if len(input_buffer) > 0:
                input_buffer.pop()
                erase_last_char()
                sys.stdout.flush()
        else:
            input_buffer.append(input_char)
            sys.stdout.write(input_char.decode())
            sys.stdout.flush()
    clear_line()
    return b"".join(input_buffer).decode()


# --- Listing 8.9 -----------------------------------------------------------
class MessageStore:
    def __init__(self, callback: Callable[[deque], Awaitable[None]], max_size: int):
        self._deque = deque(maxlen=max_size)
        self._callback = callback

    async def append(self, item):
        self._deque.append(item)
        await self._callback(self._deque)


def make_redraw(write=print) -> Callable[[deque], Awaitable[None]]:
    """Redraw the message area (top of screen) without touching the input line."""

    async def redraw_output(items: deque):
        save_cursor_position()
        move_to_top_of_screen()
        for item in items:
            delete_line()
            write(item)
        restore_cursor_position()
        sys.stdout.flush()

    return redraw_output
