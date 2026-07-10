#!/usr/bin/env python3
"""772 → 772a. Subject bars: RH always 772a grid. LH 772a only if 772 subject found."""
import json

D772 = (0, 2, 4, 5, 2, 4, 0)
D772A = (0, 2, 4, 5, 4, 2, 4, 2, 0)
ON772A = (0.5, 1.0, 1.5, 2, 2 + 1 / 3, 2 + 2 / 3, 3, 3 + 1 / 3, 3 + 2 / 3)
ROLL_G = 3 + 5 / 6
REST = 0.5
BEAT = 60 / 72
DUR1, DUR2, G_DUR = BEAT * 0.45, BEAT / 3 * 0.88, BEAT * 0.4

SUBJECT_BARS = {0, 1, 2, 4, 5, 7, 8, 9, 11, 12, 14, 15, 17, 18, 20}


def deg(m, t):
    return (m - t) % 12


def find_772(bare):
    n = len(D772)
    for i in range(len(bare) - n + 1):
        t0 = bare[i][1]
        if tuple(deg(m, t0) for _, m in bare[i : i + n]) == D772:
            return t0
    return None


def tonic_rh(bare):
    t = find_772(bare)
    if t is not None:
        return t
    bs = bare[0][0] // 4 * 4 if bare else 0
    for beat in (0.5, 0.25, 0.75, 0.0):
        for tb, m in bare:
            if abs((tb - bs) - beat) < 0.12:
                return m
    return bare[0][1]


def in_subj(t, bs):
    return bs + REST - 0.02 <= t < bs + ROLL_G + G_DUR


def emit772a(bs, tonic, vel, prefix, sid):
    out = []
    for j, d in enumerate(D772A):
        out.append({
            "id": f"{prefix}{sid}-a{j}",
            "t": round(bs + ON772A[j], 6),
            "dur": round(DUR2 if j >= 3 else DUR1, 6),
            "midi": tonic + d,
            "vel": vel,
        })
    out.append({
        "id": f"{prefix}{sid}-g",
        "t": round(bs + ROLL_G, 6),
        "dur": round(G_DUR, 6),
        "midi": tonic + 7,
        "vel": vel,
    })
    return out


def transform(events, prefix, force772a):
    events = sorted(events, key=lambda e: e["t"])
    out, sid, i = [], 0, 0
    while i < len(events):
        bar = int(events[i]["t"] // 4)
        bs, be = bar * 4, bar * 4 + 4
        chunk = []
        while i < len(events) and events[i]["t"] < be:
            chunk.append(events[i])
            i += 1
        bare = [(e["t"], e["midi"]) for e in chunk]
        do772a = bar in SUBJECT_BARS and force772a and chunk
        if not do772a or not chunk:
            out.extend(chunk)
            continue
        tonic = tonic_rh(bare)
        vel = chunk[0]["vel"]
        out.extend(emit772a(bs, tonic, vel, prefix, sid))
        sid += 1
        tail = bs + ROLL_G + G_DUR - 0.02
        for ev in chunk:
            if ev["t"] >= tail:
                out.append(ev)
    return out


def main():
    raw = json.load(open("d:/BACH/score772.json", encoding="utf-8"))
    rh = transform([e for e in raw if e["id"].startswith("rh")], "rh", True)
    lh = transform([e for e in raw if e["id"].startswith("lh")], "lh", True)
    all_ev = sorted(rh + lh, key=lambda e: (e["t"], e["midi"]))
    score_js = "const SCORE=" + json.dumps(all_ev, separators=(",", ":")) + ";"
    with open("d:/BACH/score.json", "w", encoding="utf-8") as f:
        json.dump(all_ev, f, separators=(",", ":"))
    with open("d:/BACH/score.js", "w", encoding="utf-8") as f:
        f.write(score_js + "\n")
    embed_html(score_js)
    rh_bars = len({int(e["t"] // 4) for e in rh if "-a0" in e["id"]})
    lh_bars = len({int(e["t"] // 4) for e in lh if "-a0" in e["id"]})
    print(f"772a: {len(all_ev)} events | RH={rh_bars} LH={lh_bars} subject bars | index.html ready")


def embed_html(score_js):
    import re
    path = "d:/BACH/index.html"
    with open(path, encoding="utf-8") as f:
        html = f.read()
    block = f"<script>\n{score_js}\n</script>"
    if re.search(r"const SCORE=", html):
        html = re.sub(r"<script>\s*const SCORE=[\s\S]*?</script>", block, html, count=1)
    else:
        html = html.replace('<script src="score.js"></script>', block)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    main()
