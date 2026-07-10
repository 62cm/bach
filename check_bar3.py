import json

N = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def pn(m):
    return f"{N[m % 12]}{m // 12 - 1}"

s = json.load(open("d:/BACH/score772.json"))
g = json.load(open("d:/BACH/triplet_map.json"))
b = {e["id"]: e for e in s}

for bar in [1, 2, 3, 4]:
    bs = bar * 4
    print(f"=== bar {bar + 1} RH ===")
    for e in sorted(
        [x for x in s if x["id"].startswith("rh") and bs <= x["t"] < bs + 4],
        key=lambda x: x["t"],
    ):
        print(f"  {e['id']:8} @{e['t']-bs:.3f} {pn(e['midi'])}")
    print("  triplet groups:")
    for i, grp in enumerate(g["groups"]):
        ids = [
            x for x in grp["ids"]
            if x in b and b[x]["id"].startswith("rh") and bs <= b[x]["t"] < bs + 4
        ]
        if ids:
            print(f"    g{i+1}: {ids} -> {[pn(b[x]['midi']) for x in ids]}")
