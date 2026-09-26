"""A deliberately slow recursive Fibonacci, used as a CPU-bound benchmark."""


def fib(n: int) -> int:
    if n == 1:
        return 0
    elif n == 2:
        return 1
    return fib(n - 1) + fib(n - 2)


def print_fib(number: int) -> None:
    print(f"fib({number}) is {fib(number)}")
