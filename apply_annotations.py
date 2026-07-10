#!/usr/bin/env python3
"""Apply subject_map.json — keep triplet-expanded times from score772_triplet.json."""
import json
import re
import sys


def main():
    map_path = sys.argv[1] if len(sys.argv) > 1 else "d:/BACH/subject_map.json"
    tags = json.load(open(map_path, encoding="utf-8"))["tags"]
    raw = json.load(open("d:/BACH/score772_triplet.json", encoding="utf-8"))
    tagged_ids = set(tags)
    by_bar_voice = {}
    for ev in raw:
        if ev["id"] not in tags:
            continue
        bar = int(ev["t"] // 4)
        voice = "rh" if ev["id"].startswith("rh") else "lh"
        by_bar_voice.setdefault((bar, voice), []).append((int(tags[ev["id"]]), ev))

    out = []
    used = set()
    for (bar, voice), items in sorted(by_bar_voice.items()):
        prefix = voice
        for num, ev in sorted(items, key=lambda x: x[0]):
            out.append({
                "id": f"{prefix}{bar}-n{num}",
                "t": ev["t"],
                "dur": ev["dur"],
                "midi": ev["midi"],
                "vel": ev["vel"],
            })
            used.add(ev["id"])

    for ev in raw:
        if ev["id"] in used:
            continue
        bar = int(ev["t"] // 4)
        voice = "rh" if ev["id"].startswith("rh") else "lh"
        if (bar, voice) in by_bar_voice:
            beat = ev["t"] - bar * 4
            if 0.48 <= beat < 4.05 and ev["id"] not in tagged_ids:
                if beat >= 0.5 and beat < 4.0:
                    continue
        out.append(ev)

    out.sort(key=lambda e: (e["t"], e["midi"]))
    score_js = "const SCORE=" + json.dumps(out, separators=(",", ":")) + ";"
    json.dump(out, open("d:/BACH/score.json", "w", encoding="utf-8"), separators=(",", ":"))
    open("d:/BACH/score.js", "w", encoding="utf-8").write(score_js + "\n")
    embed(score_js)
    print(f"Applied {len(tags)} tags → {len(out)} events (times unchanged)")


def embed(score_js):
    path = "d:/BACH/index.html"
    html = open(path, encoding="utf-8").read()
    block = f"<script>\n{score_js}\n</script>"
    html = re.sub(r"<script>\s*const SCORE=[\s\S]*?</script>", block, html, count=1)
    open(path, "w", encoding="utf-8").write(html)


if __name__ == "__main__":
    main()
