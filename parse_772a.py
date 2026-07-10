#!/usr/bin/env python3
"""Parse BWV 772a lilypond (triplet) → raw events, 4/4 bars."""
import json
import re
import subprocess
import sys

sys.path.insert(0, "d:/BACH")
from parse_ly import dur_to_16, relative_midi  # noqa: E402

BEATS = 4


class VoiceParser772a:
    def __init__(self, text, first_midi, voice):
        self.voice = voice
        self.first_midi = first_midi
        self.last_midi = None
        self.events = []
        self.bar = 0
        self.pos = 0.0
        self.tie = False
        self.default_dur = 2
        bars = [b.strip() for b in text.strip().split("|") if b.strip()]
        for bar_text in bars:
            self.parse_bar(bar_text)
            self.bar += 1
            self.pos = 0.0
            self.tie = False

    def emit(self, midi, dur16, is_rest=False):
        if is_rest:
            if not self.tie:
                self.pos += dur16
            self.tie = False
            return
        t = self.bar * BEATS + self.pos / 4
        self.events.append({
            "id": f"{self.voice}-{len(self.events)}",
            "t": round(t, 6),
            "dur": round((dur16 / 4) * 0.92, 6),
            "midi": midi,
            "vel": 0.72 if self.voice == "rh" else 0.52,
        })
        self.last_midi = midi
        if not self.tie:
            self.pos += dur16
        self.tie = False

    def parse_tuplet(self, inner):
        parts = re.findall(
            r"~|[a-gA-G](?:is|es)?[,']*|[a-z]+[,']*|\d+\.?|r\d+\.?",
            inner,
        )
        notes = []
        for p in parts:
            if p == "~":
                self.tie = True
                continue
            if p.startswith("r") or re.match(r"^\d+\.?$", p):
                continue
            notes.append(p)
        span = 4.0  # 3 notes in 1 beat (2 eighths)
        step = span / 3
        start = self.pos
        for i, tok in enumerate(notes[:3]):
            self.pos = start + i * step
            self.emit(relative_midi(tok, self.last_midi, self.first_midi), step * 0.95)
        self.pos = start + span
        self.tie = False

    def parse_bar(self, text):
        text = re.sub(r"%.*", "", text)
        text = re.sub(r'\\clef\s+"(?:treble|bass)"', " ", text)
        text = text.replace("~", " ~ ")
        s = text.strip()
        while s:
            s = s.lstrip()
            if not s:
                break
            if s[0] == "~":
                self.tie = True
                s = s[1:]
                continue
            if s.startswith("\\tuplet"):
                start = s.index("{")
                depth = 0
                end = start
                for j in range(start, len(s)):
                    if s[j] == "{":
                        depth += 1
                    elif s[j] == "}":
                        depth -= 1
                        if depth == 0:
                            end = j
                            break
                self.parse_tuplet(s[start + 1 : end])
                s = s[end + 1 :]
                continue
            if s[0] == "[":
                end = s.index("]")
                self.parse_group(s[1:end])
                s = s[end + 1 :]
                continue
            mr = re.match(r"^r(\d+)(\.?)", s)
            if mr:
                self.emit(0, dur_to_16(int(mr.group(1)), mr.group(2) == "."), True)
                s = s[mr.end() :]
                continue
            if s[0] == "r" and (len(s) == 1 or not s[1].isdigit()):
                self.emit(0, self.default_dur, True)
                s = s[1:]
                continue
            mn = re.match(r"^([a-gA-G](?:is|es)?[,']*|[a-z]+[,']*)", s)
            if mn:
                tok = mn.group(1)
                rest = s[mn.end() :]
                md = re.match(r"^(\d+)(\.?)", rest)
                if md:
                    d = dur_to_16(int(md.group(1)), md.group(2) == ".")
                    s = s[mn.end() + md.end() :]
                else:
                    d = self.default_dur
                    s = s[mn.end() :]
                self.emit(relative_midi(tok, self.last_midi, self.first_midi), d)
                continue
            md = re.match(r"^(\d+)(\.?)", s)
            if md:
                self.default_dur = dur_to_16(int(md.group(1)), md.group(2) == ".")
                s = s[md.end() :]
                continue
            s = s[1:]

    def parse_group(self, inner):
        parts = re.findall(
            r"~|[a-gA-G](?:is|es)?[,']*|[a-z]+[,']*|\d+\.?|r\d+\.?",
            inner,
        )
        for p in parts:
            if p == "~":
                self.tie = True
                continue
            if p.startswith("r"):
                mr = re.match(r"r(\d+)(\.?)", p)
                if mr:
                    self.emit(0, dur_to_16(int(mr.group(1)), mr.group(2) == "."), True)
                else:
                    self.emit(0, self.default_dur, True)
                continue
            md = re.match(r"^(\d+)(\.?)$", p)
            if md:
                self.default_dur = dur_to_16(int(md.group(1)), md.group(2) == ".")
                continue
            self.emit(relative_midi(p, self.last_midi, self.first_midi), self.default_dur)


def load_voices():
    with open("d:/BACH/bwv772a.ly", encoding="utf-8") as f:
        ly = f.read()

    def extract(name):
        key = f"{name} = \\relative"
        i = ly.index(key)
        i = ly.index("{", i) + 1
        depth = 1
        j = i
        while j < len(ly) and depth:
            if ly[j] == "{":
                depth += 1
            elif ly[j] == "}":
                depth -= 1
            j += 1
        return ly[i : j - 1]

    return extract("voiceone"), extract("voicetwo")


def parse_raw():
    subprocess.run([sys.executable, "d:/BACH/convert_772a_ly.py"], check=True)
    rh_text, lh_text = load_voices()
    rh = VoiceParser772a(rh_text, 72, "rh").events
    lh = VoiceParser772a(lh_text, 48, "lh").events
    return sorted(rh + lh, key=lambda x: (x["t"], x["midi"]))


def main():
    events = parse_raw()
    end = max(e["t"] + e["dur"] for e in events)
    rh1 = [(round(e["t"], 3), e["midi"]) for e in events if e["id"].startswith("rh") and e["t"] < 4]
    lh1 = [(round(e["t"], 3), e["midi"]) for e in events if e["id"].startswith("lh") and e["t"] < 4]
    print(f"772a raw: {len(events)} events, end={end:.2f} beats")
    print("bar1 RH:", rh1)
    print("bar1 LH (before shift):", lh1)
    with open("d:/BACH/score772a_raw.json", "w", encoding="utf-8") as f:
        json.dump(events, f, separators=(",", ":"))


if __name__ == "__main__":
    main()
