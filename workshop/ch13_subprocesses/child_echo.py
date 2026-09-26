"""Listing 13.11: a child program that echoes input until 'quit'."""

user_input = ""

while user_input != "quit":
    user_input = input("Enter text to echo: ")
    print(user_input)
