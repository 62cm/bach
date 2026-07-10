#!/usr/bin/env python3
"""Build score772_triplet + auto subject_map (sequential 1..N per bar/voice)."""
import json

from expand_triplets import apply_triplets


from score_fixes import apply_score_fixes


# 0-based 小节号，与 gen_score_graph.MEASURE_KIND 一致
SUBJECT_BARS = {0, 1, 2, 4, 5, 7, 8, 9, 11, 12, 14, 15, 17, 18, 20}


def build_subject_tags(score, triplets):
    """只在主题小节、前两组三连音上标 4–9；前接 1–3，后接 10。其余不标。"""
    tags = {}
    for (bar, voice), groups in sorted(triplets.items()):
        if bar not in SUBJECT_BARS or len(groups) < 2:
            continue

        g_a, g_b = groups[0], groups[1]
        bs = bar * 4
        a1, b1 = g_a["a1"], g_b["a1"]
        t_end = max(a1, b1) + 0.5
        tri_ids = {e["id"] for g in groups for e in g["exp"]}

        voice_notes = sorted(
            [e for e in score if e["id"].startswith(voice) and bs <= e["t"] < bs + 4],
            key=lambda e: e["t"],
        )
        before = [e for e in voice_notes if e["t"] < a1 - 1e-6 and e["id"] not in tri_ids]
        after = [e for e in voice_notes if e["t"] >= t_end - 1e-6 and e["id"] not in tri_ids]

        for num, e in zip([1, 2, 3], before[-3:]):
            tags[e["id"]] = num
        for num, e in zip([4, 5, 6], g_a["exp"]):
            tags[e["id"]] = num
        for num, e in zip([7, 8, 9], g_b["exp"]):
            tags[e["id"]] = num
        if after:
            tags[after[0]["id"]] = 10
        else:
            nbs = (bar + 1) * 4
            spill = sorted(
                [
                    e for e in score
                    if e["id"].startswith(voice) and nbs <= e["t"] < nbs + 1.0
                ],
                key=lambda e: e["t"],
            )
            if spill:
                tags[spill[0]["id"]] = 10

    return tags


def main():
    raw = json.load(open("d:/BACH/score772.json", encoding="utf-8"))
    groups = json.load(open("d:/BACH/triplet_map.json", encoding="utf-8"))["groups"]

    score, triplets, _ = apply_triplets(raw, groups)
    score = apply_score_fixes(score)
    tags = build_subject_tags(score, triplets)

    json.dump(score, open("d:/BACH/score772_triplet.json", "w", encoding="utf-8"), separators=(",", ":"))
    json.dump({"tags": tags}, open("d:/BACH/subject_map.json", "w", encoding="utf-8"), indent=2)
    n_grp = sum(len(v) for v in triplets.values())
    print(f"triplet groups: {n_grp} | tags: {len(tags)} | events: {len(score)}")


if __name__ == "__main__":
    main()
