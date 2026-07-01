import contextlib
import os
import sys

ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"
RESET = "\x1b[0m"


def _hsl_to_rgb(h, s, l):
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    sectors = [(c, x, 0), (x, c, 0), (0, c, x), (0, x, c), (x, 0, c), (c, 0, x)]
    r, g, b = sectors[int(h // 60) % 6]
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


def _sgr(code):
    return lambda t: f"\x1b[{code}m{t}{RESET}"


green, red, yellow, cyan, dim = (_sgr(c) for c in (32, 31, 33, 36, 2))


def format_git(info, cell_max=None):
    if info is None:
        return dim("—")
    mark = red("✗") if info.dirty else green("✔")
    if not info.has_upstream:
        sync_plain, sync = "⚲", dim("⚲")
    elif info.ahead and info.behind:
        sync_plain, sync = f"↑{info.ahead} ↓{info.behind}", yellow(f"↑{info.ahead} ↓{info.behind}")
    elif info.ahead:
        sync_plain, sync = f"↑{info.ahead}", yellow(f"↑{info.ahead}")
    elif info.behind:
        sync_plain, sync = f"↓{info.behind}", yellow(f"↓{info.behind}")
    else:
        sync_plain, sync = "≡", green("≡")
    branch = info.branch
    if cell_max is not None:
        # cell is "{mark} {branch} {sync}" -> mark + 2 spaces + sync is fixed overhead
        avail = cell_max - (3 + len(sync_plain))
        if len(branch) > avail:
            branch = branch[: max(1, avail - 1)] + "…"
    return f"{mark} {cyan(branch)} {sync}"


def term_width(default=80):
    """Columns of the controlling terminal. stdout is captured by the shell
    wrapper, so prefer stderr (where we render), then stdout, then a default."""
    for stream in (sys.stderr, sys.stdout):
        try:
            return os.get_terminal_size(stream.fileno()).columns
        except OSError:
            pass
    return default


def cell_budget(prefix_w, leaf_w):
    """Max visible width for a row's git cell so the row fits the terminal.
    Row layout: ' [x]  <path>  <cell>' -> prefix_w+leaf_w+8 before the cell."""
    return term_width() - (prefix_w + leaf_w + 8) - 1


def render_row(entry, parts, git_cell, prefix_w, leaf_w):
    prefix, leaf = parts
    letter = color(f"[{entry.letter}]", entry.rgb, bold=True)
    pad = " " * (prefix_w + leaf_w - len(prefix) - len(leaf))
    head = color(prefix, entry.rgb) if prefix else ""
    path = head + color(leaf, entry.rgb, bold=True) + pad
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
