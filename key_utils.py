#!/usr/bin/env python3
"""Per-bar key inference + diatonic triplet interpolation."""
NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

MAJOR_KEYS = [
    ("C",  (0, 2, 4, 5, 7, 9, 11)),
    ("G",  (7, 9, 11, 0, 2, 4, 6)),
    ("D",  (2, 4, 6, 7, 9, 11, 1)),
    ("A",  (9, 11, 1, 2, 4, 6, 8)),
    ("E",  (4, 6, 8, 9, 11, 1, 3)),
    ("B",  (11, 1, 3, 4, 6, 8, 10)),
    ("F",  (5, 7, 9, 10, 0, 2, 4)),
    ("Bb", (10, 0, 2, 3, 5, 7, 9)),
    ("Eb", (3, 5, 7, 8, 10, 0, 2)),
]


def infer_key_pcs(bar_midis):
    """Best-fit major scale for notes in one measure (+ accidentals actually sounding)."""
    if not bar_midis:
        return set(MAJOR_KEYS[0][1])
    pcs = [m % 12 for m in bar_midis]
    best_scale = set(MAJOR_KEYS[0][1])
    best_score = -1
    for _name, scale in MAJOR_KEYS:
        s = sum(1 for p in pcs if p in scale)
        if s > best_score:
            best_score = s
            best_scale = set(scale)
    # Keep chromatic tones that appear in the bar (temporary accidentals)
    for p in pcs:
        best_scale.add(p)
    return best_scale


def diatonic_step(cur, target, key_pcs):
    """One diatonic step from cur toward target (prefer scale tones)."""
    if cur == target:
        return cur
    sign = 1 if target > cur else -1
    for delta in range(1, 13):
        nxt = cur + sign * delta
        if nxt % 12 in key_pcs:
            if sign > 0:
                if nxt <= target:
                    return nxt
            else:
                if nxt >= target:
                    return nxt
    return target


def diatonic_path(m0, m2, key_pcs):
    """Walk diatonically from m0 to m2, always including endpoints."""
    if m0 == m2:
        return [m0, m0, m2]
    path = [m0]
    cur = m0
    guard = 0
    while cur != m2 and guard < 24:
        cur = diatonic_step(cur, m2, key_pcs)
        if path and cur == path[-1]:
            break
        path.append(cur)
        guard += 1
    if path[-1] != m2:
        path.append(m2)
    return path


def interpolate_triplet_pitches(m0, m2, key_pcs, n=3):
    """Return n pitches from m0→m2 using diatonic steps in key_pcs."""
    path = diatonic_path(m0, m2, key_pcs)
    if len(path) == n:
        return path
    if len(path) < n:
        # rare: fill by repeating nearest step
        while len(path) < n:
            path.insert(len(path) // 2, path[len(path) // 2])
        return path[:n]
    # subsample path to n points (keep endpoints)
    idxs = [round(i * (len(path) - 1) / (n - 1)) for i in range(n)]
    return [path[i] for i in idxs]


def pname(m):
    return f"{NAMES[m % 12]}{m // 12 - 1}"
