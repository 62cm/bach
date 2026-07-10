#!/usr/bin/env python3
"""Build animation data from subject_map + embed triplet score into index.html."""
import json
import re

SCORE_PATH = "d:/BACH/score772_triplet.json"
MAP_PATH = "d:/BACH/subject_map.json"
INDEX_PATH = "d:/BACH/index.html"

CYCLE_BEATS = 2.0
TOTAL_BARS = 22
TOTAL_SLOTS = TOTAL_BARS * 2  # half-bar slots


def build_slots(score_by_id, tags):
    """Half-bar cycles; bar 22's two flats merge into one horizontal platform."""
    cycle_slots = set()
    for eid, num in tags.items():
        if num != 1 or eid not in score_by_id:
            continue
        t = score_by_id[eid]["t"]
        cycle_slots.add(int(round(t / CYCLE_BEATS - 1e-9)))

    steps = []
    for slot in range(TOTAL_SLOTS):
        # bar 22 = slots 42,43 → skip 43, merge into one flat at 42
        if slot == TOTAL_SLOTS - 1:
            continue
        if slot == TOTAL_SLOTS - 2:
            steps.append({"kind": "flat", "slot": slot, "beats": 4, "bar": 22})
        elif slot in cycle_slots:
            steps.append({"kind": "cycle", "slot": slot, "beats": 2})
        else:
            steps.append({"kind": "flat", "slot": slot, "beats": 2})
    return steps, sorted(cycle_slots)


def main():
    score = json.load(open(SCORE_PATH, encoding="utf-8"))
    tags = json.load(open(MAP_PATH, encoding="utf-8"))["tags"]
    by_id = {e["id"]: e for e in score}
    steps, cycle_slots = build_slots(by_id, tags)

    score_js = "const SCORE=" + json.dumps(score, separators=(",", ":")) + ";"
    steps_js = "const STEPS=" + json.dumps(steps, separators=(",", ":")) + ";"
    tags_js = "const SUBJECT_TAGS=" + json.dumps(tags, separators=(",", ":")) + ";"

    html = open(INDEX_PATH, encoding="utf-8").read()

    # Replace SCORE script block
    score_block = f"<script>\n{score_js}\n{steps_js}\n{tags_js}\n</script>"
    if re.search(r"const SCORE=", html):
        html = re.sub(
            r"<script>\s*const SCORE=[\s\S]*?</script>",
            score_block,
            html,
            count=1,
        )
    else:
        html = html.replace("</head>", score_block + "\n</head>")

    open(INDEX_PATH, "w", encoding="utf-8").write(html)
    open("d:/BACH/score.js", "w", encoding="utf-8").write(
        score_js + "\n" + steps_js + "\n" + tags_js + "\n"
    )
    print(f"embedded {len(score)} notes | {len(cycle_slots)} cycles | {sum(1 for s in steps if s['kind']=='flat')} flat slots | {len(tags)} tags")


if __name__ == "__main__":
    main()
