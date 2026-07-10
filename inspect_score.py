import json
s = json.load(open("d:/BACH/score.json"))
for bar in range(22):
    evs = [e for e in s if bar * 4 <= e["t"] < (bar + 1) * 4]
    if not evs:
        continue
    rh = [e for e in evs if e["id"].startswith("rh")]
    lh = [e for e in evs if e["id"].startswith("lh")]
    print(f"bar {bar+1}: RH {len(rh)} LH {len(lh)}")
    print("  RH", [(round(e["t"] % 4, 2), e["midi"]) for e in rh[:12]])
    print("  LH", [(round(e["t"] % 4, 2), e["midi"]) for e in lh[:12]])
