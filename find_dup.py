import json
N = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def pn(m):
    return f"{N[m % 12]}{m // 12 - 1}"

s = json.load(open("d:/BACH/score772.json"))
for bar in range(22):
    bs = bar * 4
    for v in ["rh", "lh"]:
        ev = [e for e in s if e["id"].startswith(v) and bs + 2.5 <= e["t"] < bs + 4]
        if len(ev) >= 4:
            seq = [(round(e["t"] - bs, 2), pn(e["midi"])) for e in ev]
            names = [x[1] for x in seq]
            for i in range(len(names) - 1):
                if names[i][0] == names[i + 1][0]:  # same letter
                    print(f"bar {bar+1} {v}", seq)
                    break
