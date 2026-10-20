import re


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

    Exact match wins. With loose=True, an entry matches if it starts any word in the name;
    if several match, the longest entry wins.
    """
    if name_key in keys:
        return name_key

    if not loose:
        return None

    matches = [k for k in keys if starts_a_word(k, name_key)]
    return max(matches, key=len) if matches else None


def starts_a_word(entry, name):
    """
    True if `entry` appears in `name` right at the start of the word.

    'summer' in 'cp - summer' -> True
    'dam' in 'damage'         -> True
    'wear' in 'edge_wear'     -> True
    'on' in 'generator'       -> False
    'wear' in 'EdgeWear'      -> False
    """

    return re.search(rf"(?<![a-z0-9]){re.escape(entry)}", name) is not None
