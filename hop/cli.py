import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from . import ui
from .config import abbrev, load_config, save_config
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


def _entries(cfg):
    es = [Entry(d["path"], d["letter"]) for d in cfg["directories"]]
    es.sort(key=lambda e: e.letter)
    return es


def _path_width(entries):
    return max((len(abbrev(e.path)) for e in entries), default=0)


def run_picker(entries, with_git, prompt):
    out = sys.stderr
    width = _path_width(entries)
    n = len(entries)

    ex = None
    futures = {}
    if with_git:
        ex = ThreadPoolExecutor(max_workers=min(8, n))
        futures = {e: ex.submit(git_info, e.path) for e in entries}

    first = True
    frame = 0

    def paint():
        nonlocal first
        if not first:
            out.write(f"\x1b[{n}A")
        first = False
        for e in entries:
            if with_git:
                f = futures[e]
                cell = ui.format_git(f.result()) if f.done() else ui.dim(f"{SPINNER[frame % len(SPINNER)]} …")
            else:
                cell = ""
            out.write("\x1b[2K" + ui.render_row(e, cell, width) + "\n")
        out.flush()

    while with_git and not all(f.done() for f in futures.values()):
        paint()
        frame += 1
        time.sleep(0.08)
    paint()
    if ex:
        ex.shutdown(wait=False)

    out.write("\n" + prompt)
    out.flush()
    key = ui.read_key()
    out.write("\n")
    out.flush()

    if key in CANCEL_KEYS:
        return None
    for e in entries:
        if key == e.letter:
            return e
    return None


def cmd_pick():
    cfg = load_config()
    if not cfg["directories"]:
        eprint("hop: no directories yet. cd somewhere and run `hop add`.")
        return 0
    chosen = run_picker(_entries(cfg), with_git=True, prompt="hop to> ")
    if chosen:
        print(chosen.path)
    return 0


def cmd_list():
    cfg = load_config()
    if not cfg["directories"]:
        eprint("hop: no directories yet. cd somewhere and run `hop add`.")
        return 0
    entries = _entries(cfg)
    width = _path_width(entries)
    with ThreadPoolExecutor(max_workers=min(8, len(entries))) as ex:
        gmap = dict(zip(entries, ex.map(git_info, [e.path for e in entries])))
    for e in entries:
        eprint(ui.render_row(e, ui.format_git(gmap[e]), width))
    return 0


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
    return cmd_pick()
