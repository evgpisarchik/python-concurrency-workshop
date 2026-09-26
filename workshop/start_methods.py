"""Module-level state for the start-method demo in notebook 18.

A process started with `fork` gets a copy of the parent's memory, so it sees changes the parent made to
STATE. With `spawn` or `forkserver`, the child imports this module fresh and sees the original value.
"""

STATE = {"config": "loaded from file"}


def send_state(connection) -> None:
    connection.send(STATE["config"])
