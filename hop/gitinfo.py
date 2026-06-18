import subprocess
from dataclasses import dataclass


@dataclass
class GitInfo:
    branch: str
    dirty: bool
    ahead: int
    behind: int
    has_upstream: bool


def _run(path, *args, timeout=4):
    return subprocess.run(
        ["git", "-C", path, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def git_info(path):
    """Return GitInfo for a repo, or None if path is not a git work tree / on error."""
    try:
        r = _run(path, "rev-parse", "--is-inside-work-tree")
        if r.returncode != 0 or r.stdout.strip() != "true":
            return None

        branch = _run(path, "branch", "--show-current").stdout.strip() or "(detached)"
        dirty = bool(_run(path, "status", "--porcelain").stdout.strip())

        ahead = behind = 0
        has_upstream = False
        rl = _run(path, "rev-list", "--left-right", "--count", "@{u}...HEAD")
        if rl.returncode == 0 and rl.stdout.strip():
            parts = rl.stdout.split()
            if len(parts) == 2:
                behind, ahead = int(parts[0]), int(parts[1])
                has_upstream = True

        return GitInfo(branch, dirty, ahead, behind, has_upstream)
    except Exception:
        return None
