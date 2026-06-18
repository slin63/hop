import contextlib
import os
import sys
from .config import display_parts

ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"
RESET = "\x1b[0m"


def _hsl_to_rgb(h, s, l):
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return round((r + m) * 255), round((g + m) * 255), round((b + m) * 255)


def letter_rgb(letter):
    i = ALPHABET.find(letter)
    if i < 0:
        i = ord(letter[0]) % len(ALPHABET)
    hue = (i * 360.0 / len(ALPHABET)) % 360
    return _hsl_to_rgb(hue, 0.6, 0.65)


def color(text, rgb, bold=False):
    r, g, b = rgb
    prefix = ("\x1b[1m" if bold else "") + f"\x1b[38;2;{r};{g};{b}m"
    return f"{prefix}{text}{RESET}"


def green(t):
    return f"\x1b[32m{t}{RESET}"


def red(t):
    return f"\x1b[31m{t}{RESET}"


def yellow(t):
    return f"\x1b[33m{t}{RESET}"


def cyan(t):
    return f"\x1b[36m{t}{RESET}"


def dim(t):
    return f"\x1b[2m{t}{RESET}"


def format_git(info):
    if info is None:
        return dim("—")
    mark = red("✗") if info.dirty else green("✔")
    branch = cyan(info.branch)
    if not info.has_upstream:
        sync = dim("⚲")
    elif info.ahead and info.behind:
        sync = yellow(f"↑{info.ahead} ↓{info.behind}")
    elif info.ahead:
        sync = yellow(f"↑{info.ahead}")
    elif info.behind:
        sync = yellow(f"↓{info.behind}")
    else:
        sync = green("≡")
    return f"{mark} {branch} {sync}"


def render_row(entry, git_cell, prefix_w, leaf_w):
    prefix, leaf = display_parts(entry.path)
    letter = color(f"[{entry.letter}]", entry.rgb, bold=True)
    path = color(prefix.rjust(prefix_w) + leaf.ljust(leaf_w), entry.rgb)
    cell = f"  {git_cell}" if git_cell else ""
    return f" {letter}  {path}{cell}"


@contextlib.contextmanager
def raw_tty():
    """Yield a raw-mode tty fd for non-blocking key reads, or None if no tty."""
    import termios
    import tty

    try:
        fd = os.open("/dev/tty", os.O_RDONLY)
    except OSError:
        yield None
        return
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        yield fd
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        os.close(fd)


def poll_key(fd, timeout):
    """Wait up to `timeout` seconds (None = forever) for a keypress on `fd`.
    Returns the char, or None if the wait timed out."""
    import select

    r, _, _ = select.select([fd], [], [], timeout)
    if not r:
        return None
    data = os.read(fd, 1)
    return data.decode("utf-8", "ignore") if data else None


def read_key():
    """Blocking single-keypress read, used only in the non-tty fallback."""
    data = sys.stdin.buffer.read(1)
    return data.decode("utf-8", "ignore") if data else ""
