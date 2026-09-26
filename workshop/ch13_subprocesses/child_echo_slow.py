"""Listing 13.13: an echo program with a random number of slow, repeated outputs."""

import time
from random import randrange

user_input = ""

while user_input != "quit":
    user_input = input("Enter text to echo: ")
    for i in range(randrange(10)):
        time.sleep(0.5)
        print(user_input)
