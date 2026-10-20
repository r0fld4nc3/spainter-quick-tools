def parse_names(text):
    """'a, b ,, c' -> ['a', 'b', 'c'] (empty entries and case-insensitive duplicates removed)"""
    names, seen = [], set()

    for part in text.split(","):
        part: str = part.strip()
        key: str = part.casefold()
        if part and key not in seen:
            seen.add(key)
            names.append(part)

    return names


def find_matching_key(name_key, keys, loose=False):
    """
    Best entry in `keys` for an already-casefolded name, or None.

    Exact match wins. With loose=True, the longest entry the name starts with wins.
    """
    if name_key in keys:
        return name_key

    if not loose:
        return None

    matches = [k for k in keys if name_key.startswith(k)]
    return max(matches, key=len) if matches else None
