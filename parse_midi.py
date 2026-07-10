#!/usr/bin/env python3
"""Parse jsbach.net BWV 772 MIDI → score772.json (RH/LH aligned, authoritative timing)."""
import json
import sys

try:
    import mido
except ImportError:
    raise SystemExit("pip install mido")

NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
RH_SHIFT = 12  # MIDI treble is written one octave lower than our display octave


def parse_midi(path, rh_shift=RH_SHIFT):
    mf = mido.MidiFile(path)
    tpb = mf.ticks_per_beat
    out = []
    for ti in (1, 2):
        voice = "rh" if ti == 1 else "lh"
        tcur = 0.0
        active = {}
        idx = 0
        for msg in mf.tracks[ti]:
            tcur += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                active[msg.note] = (tcur / tpb, msg.velocity)
            elif msg.type in ("note_off", "note_on") and (
                msg.type == "note_off" or msg.velocity == 0
            ):
                if msg.note not in active:
                    continue
                st, vel = active.pop(msg.note)
                dur = tcur / tpb - st
                midi = msg.note + (rh_shift if voice == "rh" else 0)
                out.append({
                    "id": f"{voice}-{idx}",
                    "t": round(st, 6),
                    "dur": round(max(dur, 0.01) * 0.92, 6),
                    "midi": midi,
                    "vel": round(0.72 if voice == "rh" else 0.52, 2),
                })
                idx += 1
    out.sort(key=lambda e: (e["t"], e["midi"]))
    return out


def pname(m):
    return f"{NAMES[m % 12]}{m // 12 - 1}"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "d:/BACH/bwv772.mid"
    events = parse_midi(path)
    end = max(e["t"] + e["dur"] for e in events)
    rh = sum(1 for e in events if e["id"].startswith("rh"))
    lh = sum(1 for e in events if e["id"].startswith("lh"))
    print(f"MIDI {path}: RH {rh} LH {lh} total {len(events)} end={end:.2f} beats")

    for out in ("d:/BACH/score772.json", "d:/BACH/score.json"):
        json.dump(events, open(out, "w", encoding="utf-8"), separators=(",", ":"))
    js = "const SCORE=" + json.dumps(events, separators=(",", ":")) + ";\n"
    open("d:/BACH/score.js", "w", encoding="utf-8").write(js)

    b1 = [e for e in events if e["t"] < 4]
    print("RH bar1:", [(round(e["t"], 2), pname(e["midi"])) for e in b1 if e["id"].startswith("rh")])
    print("LH bar1:", [(round(e["t"], 2), pname(e["midi"])) for e in b1 if e["id"].startswith("lh")])
    b5 = [e for e in events if 16 <= e["t"] < 20]
    print("RH bar5 2nd half:", [(round(e["t"] - 16, 2), pname(e["midi"])) for e in b5 if e["id"].startswith("rh") and e["t"] >= 18])
    print("LH bar5:", [(round(e["t"] - 16, 2), pname(e["midi"])) for e in b5 if e["id"].startswith("lh")])


if __name__ == "__main__":
    main()
