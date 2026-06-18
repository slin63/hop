import string

POOL = string.ascii_lowercase + string.digits


def assign_letter(basename, taken):
    """Stable letter for a dir: prefer chars from its name (first letter first),
    then any free alnum. Returns None if all 36 slots are taken."""
    candidates = []
    for ch in basename.lower():
        if ch in POOL and ch not in candidates:
            candidates.append(ch)
    for ch in POOL:
        if ch not in candidates:
            candidates.append(ch)
    for ch in candidates:
        if ch not in taken:
            return ch
    return None
