#!/usr/bin/env python3
"""Apply user subject_map — tags only. Never retime or re-expand triplets."""
import json
import sys

from expand_triplets import apply_triplets
from score_fixes import apply_score_fixes


def main():
    src_map = sys.argv[1] if len(sys.argv) > 1 else "d:/BACH/subject_map.json"
    raw = json.load(open("d:/BACH/score772.json", encoding="utf-8"))
    groups = json.load(open("d:/BACH/triplet_map.json", encoding="utf-8"))["groups"]

    score, _, _ = apply_triplets(raw, groups)
    score = apply_score_fixes(score)

    tags = json.load(open(src_map, encoding="utf-8"))["tags"]
    by_id = {e["id"]: e for e in score}
    missing = [eid for eid in tags if eid not in by_id and not eid.startswith("rh-fix") and not eid.startswith("lh-fix")]
    if missing:
        print(f"warn: {len(missing)} tagged ids not in score (stale tags ignored)")

    json.dump({"tags": tags}, open("d:/BACH/subject_map.json", "w", encoding="utf-8"), indent=2)
    json.dump(score, open("d:/BACH/score772_triplet.json", "w", encoding="utf-8"), separators=(",", ":"))
    open("d:/BACH/score.js", "w", encoding="utf-8").write(
        "const SCORE=" + json.dumps(score, separators=(",", ":")) + ";\n"
    )
    print(f"Applied subject_map | {len(tags)} tags | {len(score)} events | anchors untouched")


if __name__ == "__main__":
    main()
