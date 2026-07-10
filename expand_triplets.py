#!/usr/bin/env python3
"""Each marked pair → one triplet (3 notes in 0.5 beat from A1). No pair-picking."""
import json
import sys

from key_utils import infer_key_pcs, interpolate_triplet_pitches, pname


def voice_of(eid):
    return "rh" if eid.startswith("rh") else "lh"


def bar_midis(all_events, bar):
    bs, be = bar * 4, bar * 4 + 4
    return [e["midi"] for e in all_events if bs <= e["t"] < be]


def groups_by_bar_voice(groups, by_id):
    out = {}
    for gi, grp in enumerate(groups):
        ids = [i for i in grp["ids"] if i in by_id]
        if len(ids) < 2:
            continue
        by_v = {}
        for i in ids:
            by_v.setdefault(voice_of(i), []).append(i)
        for voice, vids in by_v.items():
            if len(vids) < 2:
                continue
            bar = int(by_id[vids[0]]["t"] // 4)
            out.setdefault((bar, voice), []).append({"gi": gi, "ids": vids})
    for key in out:
        out[key].sort(key=lambda g: min(by_id[i]["t"] for i in g["ids"]))
    return out


EIGHTH = 0.5


def expand_triplet(evs, key_pcs, tag):
    """A1 不动，3 音在半拍内均分。"""
    e = sorted(evs, key=lambda x: x["t"])
    a1 = e[0]["t"]
    vel = e[0]["vel"]
    step = EIGHTH / 3
    note_dur = round(step * 0.92, 6)
    pitches = interpolate_triplet_pitches(e[0]["midi"], e[-1]["midi"], key_pcs, 3)
    out = []
    for j, midi in enumerate(pitches):
        out.append({
            "id": f"{tag}-n{j}",
            "t": round(a1 + j * step, 6),
            "dur": note_dur,
            "midi": midi,
            "vel": vel,
        })
    return out, a1


def apply_triplets(raw, groups):
    by_id = {e["id"]: e for e in raw}
    gbv = groups_by_bar_voice(groups, by_id)
    remove = set()
    insert = []
    triplets = {}  # (bar, voice) -> [{exp, a1, gi}, ...]

    for (bar, voice), grps in gbv.items():
        key_pcs = infer_key_pcs(bar_midis(raw, bar))
        bs = bar * 4
        bar_tris = []
        for ord_i, g in enumerate(grps):
            evs = [by_id[i] for i in g["ids"]]
            tag = f"{voice}-b{bar}-t{ord_i}"
            exp, a1 = expand_triplet(evs, key_pcs, tag)
            bar_tris.append({"exp": exp, "a1": a1, "gi": g["gi"], "ids": g["ids"]})

            for i in g["ids"]:
                remove.add(i)
            for e in raw:
                if not e["id"].startswith(voice):
                    continue
                if bs <= e["t"] < bs + 4 and a1 - 1e-6 <= e["t"] < a1 + EIGHTH:
                    remove.add(e["id"])

            insert.extend(exp)
            print(
                f"bar{bar + 1} {voice} t{ord_i + 1}/{len(grps)} "
                f"A1={round(a1 - bs, 3)} → {' '.join(pname(x['midi']) for x in exp)}"
            )
        triplets[(bar, voice)] = bar_tris

    out = [e for e in raw if e["id"] not in remove]
    out.extend(insert)
    out.sort(key=lambda e: (e["t"], e["midi"]))
    return out, triplets, by_id


# 兼容旧名
apply_sextuplets = apply_triplets


def main():
    map_path = sys.argv[1] if len(sys.argv) > 1 else "d:/BACH/triplet_map.json"
    raw = json.load(open("d:/BACH/score772.json", encoding="utf-8"))
    groups = json.load(open(map_path, encoding="utf-8")).get("groups", [])

    out, _, _ = apply_triplets(raw, groups)
    json.dump(out, open("d:/BACH/score772_triplet.json", "w", encoding="utf-8"), separators=(",", ":"))
    open("d:/BACH/score.js", "w", encoding="utf-8").write(
        "const SCORE=" + json.dumps(out, separators=(",", ":")) + ";\n"
    )
    n = sum(len(v) for v in groups_by_bar_voice(groups, {e["id"]: e for e in raw}).values())
    print(f"→ {len(out)} events, {n} triplet groups → score772_triplet.json")


if __name__ == "__main__":
    main()
