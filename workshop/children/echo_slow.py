"""Interactive echo: after each input prints it 0-9 times, slowly. Type 'quit' to exit."""

import time
from random import randrange

user_input = ""
while user_input != "quit":
    user_input = input("Enter text to echo: ")
    for _ in range(randrange(10)):
        time.sleep(0.2)
        print(user_input)
