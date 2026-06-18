import json
import os
import sys
from pathlib import Path


def config_path():
    env = os.environ.get("HOP_CONFIG")
    if env:
        return Path(env)
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "hop" / "config.json"


def load_config():
    p = config_path()
    if not p.exists():
        return {"version": 1, "directories": []}
    try:
        data = json.loads(p.read_text())
    except Exception:
        print(f"hop: corrupt config at {p}, starting fresh.", file=sys.stderr)
        return {"version": 1, "directories": []}
    data.setdefault("directories", [])
    return data


def save_config(cfg):
    p = config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cfg, indent=2) + "\n")


def abbrev(path):
    home = str(Path.home())
    if path == home or path.startswith(home + os.sep):
        return "~" + path[len(home):]
    return path
