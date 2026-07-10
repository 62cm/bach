import json

N = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
SUBJECT = {0, 1, 2, 4, 5, 7, 8, 9, 11, 12, 14, 15, 17, 18, 20}

def pn(m):
    return f"{N[m % 12]}{m // 12 - 1}"

s = json.load(open("d:/BACH/score772.json"))
g = json.load(open("d:/BACH/triplet_map.json"))
b = {e["id"]: e for e in s}

from collections import defaultdict
gbv = defaultdict(list)
for i, grp in enumerate(g["groups"]):
    ids = [x for x in grp["ids"] if x in b]
    if not ids or len({x[:2] for x in ids}) > 1:
        continue
    v = ids[0][:2]
    bar = int(b[ids[0]]["t"] // 4)
    gbv[(bar, v)].append({"i": i + 1, "ids": ids, "t": min(b[x]["t"] for x in ids)})

for bar in sorted(SUBJECT):
    print(f"bar {bar+1}:")
    for v in ("rh", "lh"):
        grps = gbv.get((bar, v), [])
        if not grps:
            continue
        beats = [round(x["t"] - bar * 4, 2) for x in grps]
        print(f"  {v}: {len(grps)} groups @ {beats}")
