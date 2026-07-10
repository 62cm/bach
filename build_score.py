#!/usr/bin/env python3
"""BWV 772a triplet score — 4/4 bars, LH after RH note 10 in subject bars."""
import json
import sys

sys.path.insert(0, "d:/BACH")
from parse_772a import parse_raw  # noqa: E402

BEATS = 4
SUBJECT_BARS = {0, 1, 2, 4, 5, 7, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21}
LH_PICKUP = 0.25  # r16 after RH 10th


def fix_lh_after_rh10(events):
    rh = [e for e in events if e["id"].startswith("rh")]
    lh = [e for e in events if e["id"].startswith("lh")]
    lh_ids = {e["id"] for e in lh}
    out = [e for e in events if e["id"] not in lh_ids]

    by_bar = {}
    for e in lh:
        by_bar.setdefault(int(e["t"] // BEATS), []).append(e)

    for b, lh_bar in by_bar.items():
        if b not in SUBJECT_BARS:
            out.extend(lh_bar)
            continue
        rh_bar = sorted(
            [e for e in rh if b * BEATS <= e["t"] < (b + 1) * BEATS],
            key=lambda x: x["t"],
        )
        if len(rh_bar) < 10:
            out.extend(lh_bar)
            continue
        tenth = rh_bar[9]
        anchor = tenth["t"] + tenth["dur"] + LH_PICKUP
        first = min(e["t"] for e in lh_bar)
        shift = anchor - first
        for e in lh_bar:
            out.append({**e, "t": round(e["t"] + shift, 6)})
    return sorted(out, key=lambda x: (x["t"], x["midi"]))


def main():
    raw = parse_raw()
    score = fix_lh_after_rh10(raw)
    end = max(e["t"] + e["dur"] for e in score)
    rh1 = [(round(e["t"], 2), e["midi"]) for e in score if e["id"].startswith("rh") and e["t"] < 4]
    lh1 = [(round(e["t"], 2), e["midi"]) for e in score if e["id"].startswith("lh") and e["t"] < 4]
    print(f"772a: {len(score)} events, {end:.2f} beats (4/4 triplet)")
    print("bar1 RH:", rh1)
    print("bar1 LH:", lh1)
    for path in ("d:/BACH/score.json", "d:/BACH/score772a.json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(score, f, separators=(",", ":"))
    with open("d:/BACH/score.js", "w", encoding="utf-8") as f:
        f.write("const SCORE=" + json.dumps(score, separators=(",", ":")) + ";\n")


if __name__ == "__main__":
    main()
