import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from . import ui
from .config import abbrev, display_parts, load_config, save_config
from .gitinfo import git_info
from .letters import assign_letter

SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
CANCEL_KEYS = ("\x03", "\x1b", "q", "")


def eprint(*a):
    print(*a, file=sys.stderr)


@dataclass(frozen=True)
class Entry:
    path: str
    letter: str

    @property
    def rgb(self):
        return ui.letter_rgb(self.letter)


NO_DIRS = "hop: no directories yet. cd somewhere and run `hop add`."


def _entries(cfg):
    es = [Entry(d["path"], d["letter"]) for d in cfg["directories"]]
    es.sort(key=lambda e: e.letter)
    return es


def _load_entries():
    """Sorted entries from config, or None (after a message) if the list is empty."""
    cfg = load_config()
    if not cfg["directories"]:
        eprint(NO_DIRS)
        return None
    return _entries(cfg)


def _path_widths(entries):
    """Max prefix and leaf widths so leaf names start at a common column."""
    pw = lw = 0
    for e in entries:
        prefix, leaf = display_parts(e.path)
        pw = max(pw, len(prefix))
        lw = max(lw, len(leaf))
    return pw, lw


def _start_git_workers(entries):
    """Resolve git status in daemon threads (never block process exit).
    Returns (results, done) dicts updated in place as work completes."""
    results, done = {}, {}
    sem = threading.Semaphore(8)

    def worker(e):
        try:
            with sem:
                results[e] = git_info(e.path)
        finally:
            done[e] = True

    for e in entries:
        threading.Thread(target=worker, args=(e,), daemon=True).start()
    return results, done


def _match(key, entries):
    if key in CANCEL_KEYS or key is None:
        return None
    for e in entries:
        if key == e.letter:
            return e
    return None


def run_picker(entries, with_git, prompt):
    out = sys.stderr
    prefix_w, leaf_w = _path_widths(entries)
    n = len(entries)
    results, done = _start_git_workers(entries) if with_git else ({}, {})

    def cell_for(e, frame):
        if not with_git:
            return ""
        if done.get(e):
            return ui.format_git(results.get(e))
        return ui.dim(f"{SPINNER[frame % len(SPINNER)]} …")

    def paint(frame, first):
        if not first:
            out.write(f"\r\x1b[{n}A")
        for e in entries:
            out.write("\x1b[2K" + ui.render_row(e, cell_for(e, frame), prefix_w, leaf_w) + "\r\n")
        out.write("\x1b[2K" + prompt)
        out.flush()

    with ui.raw_tty() as fd:
        if fd is None:  # non-interactive fallback
            paint(0, True)
            key = ui.read_key()
        else:
            key = None
            frame = 0
            first = True
            while True:
                paint(frame, first)
                first = False
                # git still resolving -> animate; otherwise block until a key
                all_done = not with_git or all(done.get(e) for e in entries)
                ch = ui.poll_key(fd, None if all_done else 0.08)
                if ch is not None:
                    key = ch
                    break
                frame += 1

    out.write("\n")
    out.flush()
    return _match(key, entries)


def cmd_pick():
    entries = _load_entries()
    if entries is None:
        return 0
    chosen = run_picker(entries, with_git=True, prompt="hop to> ")
    if chosen:
        print(chosen.path)
    return 0


def cmd_list():
    entries = _load_entries()
    if entries is None:
        return 0
    prefix_w, leaf_w = _path_widths(entries)
    with ThreadPoolExecutor(max_workers=min(8, len(entries))) as ex:
        gmap = dict(zip(entries, ex.map(git_info, [e.path for e in entries])))
    for e in entries:
        eprint(ui.render_row(e, ui.format_git(gmap[e]), prefix_w, leaf_w))
    return 0


def cmd_go(args):
    if not args:
        eprint("hop: usage: hop go <letter>")
        return 1
    letter = args[0]
    for e in _entries(load_config()):
        if e.letter == letter:
            print(e.path)
            return 0
    eprint(f"hop: no directory for letter '{letter}'")
    return 1


def cmd_add(args):
    target = args[0] if args else os.getcwd()
    path = os.path.realpath(target)
    if not os.path.isdir(path):
        eprint(f"hop: not a directory: {path}")
        return 1
    cfg = load_config()
    dirs = cfg["directories"]
    if any(d["path"] == path for d in dirs):
        eprint(f"hop: already added: {abbrev(path)}")
        return 0
    taken = {d["letter"] for d in dirs}
    letter = assign_letter(os.path.basename(path) or path, taken)
    if letter is None:
        eprint("hop: directory list full (36 max).")
        return 1
    dirs.append({"path": path, "letter": letter})
    save_config(cfg)
    eprint(f"hop: added [{letter}] {abbrev(path)}")
    return 0


def cmd_remove():
    cfg = load_config()
    if not cfg["directories"]:
        eprint("hop: nothing to remove.")
        return 0
    chosen = run_picker(_entries(cfg), with_git=False, prompt="remove which> ")
    if not chosen:
        return 0
    cfg["directories"] = [d for d in cfg["directories"] if d["path"] != chosen.path]
    save_config(cfg)
    eprint(f"hop: removed [{chosen.letter}] {abbrev(chosen.path)}")
    return 0


HELP = """hop - jump to predefined directories with single-letter shortcuts

usage:
  hop              list dirs + git status, press a letter to cd there
  hop go <letter>  cd straight to that letter's dir, no prompt (alias: -g)
  hop add [path]   add the current dir (or PATH) to the list
  hop remove       pick a dir to remove (alias: rm)
  hop list         print the list without prompting
  hop -h           show this help

config: $HOP_CONFIG or ${XDG_CONFIG_HOME:-~/.config}/hop/config.json
"""


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else None

    if cmd in ("-h", "--help", "help"):
        eprint(HELP)
        return 0
    if cmd == "add":
        return cmd_add(argv[1:])
    if cmd in ("remove", "rm"):
        return cmd_remove()
    if cmd == "list":
        return cmd_list()
    if cmd in ("go", "-g"):
        return cmd_go(argv[1:])
    return cmd_pick()
