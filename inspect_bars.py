import json
N = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def pn(m):
    return f"{N[m % 12]}{m // 12 - 1}"

s = json.load(open("d:/BACH/score772.json"))
for bar in [5, 11, 12, 15, 16]:
    bs = bar * 4
    print("=== bar", bar + 1)
    for v in ["rh", "lh"]:
        ev = [e for e in s if e["id"].startswith(v) and bs <= e["t"] < bs + 4]
        print(v, [(e["id"], round(e["t"] - bs, 3), pn(e["midi"])) for e in ev])
