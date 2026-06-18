import string

POOL = string.ascii_lowercase + string.digits


def assign_letter(basename, taken):
    """Stable letter for a dir: prefer chars from its name (first letter first),
    then any free alnum. Returns None if all 36 slots are taken."""
    seen = set()
    for ch in basename.lower() + POOL:
        if ch in POOL and ch not in seen:
            seen.add(ch)
            if ch not in taken:
                return ch
    return None
