"""Terminal helpers: single-keypress input (for clean reaction times), prompts."""

import os
import sys


def getkey(valid):
    """Wait for one key in `valid` and return it, without needing Enter.

    Falls back to line input when stdin isn't an interactive terminal.
    """
    if not sys.stdin.isatty():
        while True:
            line = sys.stdin.readline()
            if not line:
                raise EOFError
            if line.strip()[:1] in valid:
                return line.strip()[:1]
    if os.name == "nt":
        import msvcrt
        while True:
            ch = msvcrt.getwch()
            if ch in ("\x03", "\x1a"):
                raise KeyboardInterrupt
            if ch in valid:
                return ch
    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch in ("\x03", "\x04"):
                raise KeyboardInterrupt
            if ch in valid:
                return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def ask(prompt, choices=None):
    """Line input. With `choices`, repeat until the answer starts with one of them."""
    while True:
        ans = input(prompt).strip()
        if choices is None or ans[:1].lower() in choices:
            return ans if choices is None else ans[:1].lower()


def clear():
    if not sys.stdout.isatty():
        print("\n" * 3, end="", flush=True)
    elif os.name == "nt":
        os.system("cls")
    else:
        print("\033[2J\033[H", end="", flush=True)


def wrap(text, indent="  ", width=78):
    import textwrap
    return "\n".join(textwrap.fill(p, width, initial_indent=indent, subsequent_indent=indent)
                     for p in str(text).split("\n"))
