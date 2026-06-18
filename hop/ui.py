import sys
from .config import abbrev

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


def yellow(t):
    return f"\x1b[33m{t}{RESET}"


def cyan(t):
    return f"\x1b[36m{t}{RESET}"


def dim(t):
    return f"\x1b[2m{t}{RESET}"


def format_git(info):
    if info is None:
        return dim("—")
    mark = "❌" if info.dirty else "✅"
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


def render_row(entry, git_cell, path_width):
    letter = color(f"[{entry.letter}]", entry.rgb, bold=True)
    path = color(abbrev(entry.path).ljust(path_width), entry.rgb)
    cell = f"   {git_cell}" if git_cell else ""
    return f" {letter}  {path}{cell}"


def read_key():
    """Read a single keypress from the controlling terminal (raw mode)."""
    import termios
    import tty

    try:
        tty_in = open("/dev/tty", "rb", buffering=0)
    except OSError:
        data = sys.stdin.buffer.read(1)
        return data.decode("utf-8", "ignore") if data else ""

    fd = tty_in.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = tty_in.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        tty_in.close()
    return ch.decode("utf-8", "ignore") if ch else ""
