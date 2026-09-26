"""Listing 7.12: a minimal Tkinter app, whose mainloop is its own event loop.

Use case: GUI toolkits own the main thread with a blocking event loop, so
asyncio can't run there. See 13_load_tester_app.py for how to combine them.

Run: uv run python -m workshop.ch07_threads_and_blocking_io.12_tkinter_hello   (needs a display)
"""

import tkinter
from tkinter import ttk

window = tkinter.Tk()
window.title("Hello world app")
window.geometry("200x100")


def say_hello():
    print("Hello there!")


hello_button = ttk.Button(window, text="Say hello", command=say_hello)
hello_button.pack()

window.mainloop()
