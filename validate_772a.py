#!/usr/bin/env python3
"""Validate subject bars against canonical 772a grid."""
import json
import re

ON772A = (
    0.5, 1.0, 1.5,
    2 + 0 / 3, 2 + 1 / 3, 2 + 2 / 3,
    3 + 0 / 3, 3 + 1 / 3, 3 + 2 / 3,
    4.0,
)
SUBJECT_BARS = {0, 1, 2, 4, 5, 7, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21}
TOL = 0.05


def nearest_grid(beat):
    return min(ON772A, key=lambda g: abs(g - beat))


def main():
    score = json.load(open("d:/BACH/score.json", encoding="utf-8"))
    ok = 0
    bad = 0
    for b in sorted(SUBJECT_BARS):
        bs = b * 4
        for voice in ("rh", "lh"):
            subj = [
                e for e in score
                if e["id"].startswith(voice) and re.search(r"-s\d+-[ag]", e["id"])
                and bs <= e["t"] < bs + 4
            ]
            if not subj:
                continue
            hits = 0
            for e in subj:
                beat = e["t"] - bs
                if abs(beat - nearest_grid(beat)) < TOL:
                    hits += 1
            n = len(subj)
            print(f"bar {b+1} {voice}: {hits}/{n} grid hits")
            if hits >= n - 1:
                ok += 1
            else:
                bad += 1
    print(f"summary: {ok} ok, {bad} weak")


if __name__ == "__main__":
    main()
