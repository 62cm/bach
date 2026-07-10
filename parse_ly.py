#!/usr/bin/env python3
"""Parse Mutopia BWV 772 lilypond → score.json (22 bars, both voices)."""
import json
import re

VOICEONE = r"""r16 c[ d e] f[ d e c] g'8[ c b c] |
d16[ g, a b] c[ a b g] d'8[ g f g] |
e16[ a g f] e[ g f a] g[ f e d] c[ e d f] |
e[ d c b] a[ c b d] c[ b a g] fis[ a g b] |
a8[ d,] c'8.[ d16] b[ a g fis] e[ g fis a] |
g[ b a c] b[ d c e] d[ b32 c d16 g] b,8[ a16 g] |
g8 r r4 r16 g[ a b] c[ a b g] |
fis8 r r4 r16 a[ b c] d[ b c a] |
b8 r r4 r16 d[ c b] a[ c b d] |
c8 r r4 r16 e[ d c] b[ d cis e] |
d8[ cis d e] f[ a, b cis] |
d[ fis, gis a] b[ c] d4 ~ |
d16[ e, fis gis] a[ fis gis e] e'[ d c e] d[ c b d] |
c[ a' gis b] a[ e f d] gis,[ f' e d] c8[ b16 a] |
a16[ a' g f] e[ g f a] g2 ~ |
g16[ e f g] a[ f g e] f2 ~ |
f16[ g f e] d[ f e g] f2 ~ |
f16[ d e f] g[ e f d] e2 ~ |
e16[ c d e] f[ d e c] d[ e f g] a[ f g e] |
f[ g a b] c[ a b g] c8[ g] e[ d16 c] |
c[ bes a g] f[ a g bes] a[ b c e,] d[ c' f, b] |
c1 |"""

VOICETWO = r"""r2 r16 c[ d e] f[ d e c] |
g'8[ g,] r4 r16 g'[ a b] c[ a b g] |
c8[ b c d] e[ g, a b] |
c[ e, fis g] a[ b] c4 ~ |
c16[ d, e fis] g[ e fis d] g8[ b, c d] |
e[ fis g e] b8.[ c16] d8[ d,] |
r16 g[ a b] c[ a b g] d'8[ g fis g] |
a16[ d, e fis] g[ e fis d] a'8[ d c d] |
g,16[ g' f e] d[ f e g] f8[ e f d] |
e16[ a g f] e[ g f a] g8[ f g e] |
f16[ bes a g] f[ a g bes] a[ g f e] d[ f e g] |
f[ e d c] b[ d c e] d[ c b a] gis[ b a c] |
b8[ e,] d'8.[ e16] c[ b a g] fis[ a gis b] |
a[ c b d] c[ e d f] e8[ a, e' e,] |
a8[ a,] r4 r16 e''16[ d c] b[ d cis e] |
d2 ~ d16[ a b c] d[ b c a] |
b2 ~ b16[ d c b] a[ c b d] |
c2 ~ c16[ g a bes] c[ a bes g] |
a8[ bes a g] f[ d' c bes] |
a[ f' e d] e16[ d, e f] g[ e f d] |
e8[ c d e] f16[ d e f] g8[ g,] |
c1 |"""

PC = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
SCALE = {0: 0, 2: 1, 4: 2, 5: 3, 7: 4, 9: 5, 11: 6}


def scale_idx(m):
    pc = m % 12
    if pc not in SCALE:
        return m  # chromatic fallback for fis/gis/bes etc.
    return (m // 12) * 7 + SCALE[pc]


def dur_to_16(num, dotted=False):
    table = {1: 16, 2: 8, 4: 4, 8: 2, 16: 1, 32: 0.5}
    return table.get(num, 1) * (1.5 if dotted else 1)


def note_pc(tok):
    tok = tok.lower()
    for name in ("cis", "dis", "fis", "gis", "ais", "bes", "ees", "aes"):
        if tok.startswith(name):
            base = PC[name[0]]
            alt = 1 if name.endswith("is") else -1
            marks = tok[len(name):]
            return base + alt, marks
    m = re.match(r"^([a-g])(is|es)?([,']*)$", tok)
    if not m:
        return None, ""
    letter, alt, marks = m.group(1), m.group(2) or "", m.group(3) or ""
    sem = PC[letter] + (1 if alt == "is" else -1 if alt == "es" else 0)
    return sem, marks


def relative_midi(tok, last_midi, first_midi):
    sem, marks = note_pc(tok)
    if sem is None:
        return last_midi
    if last_midi is None:
        midi = first_midi
    else:
        best = last_midi
        best_d = 10**9
        for cand in range(last_midi - 12, last_midi + 13):
            if cand % 12 != sem:
                continue
            d = abs(scale_idx(cand) - scale_idx(last_midi))
            if d < best_d:
                best_d = d
                best = cand
        midi = best
    for ch in marks:
        midi += 12 if ch == "'" else -12
    return midi


class VoiceParser:
    def __init__(self, text, first_midi, voice):
        self.voice = voice
        self.first_midi = first_midi
        self.last_midi = None
        self.events = []
        self.bar = 0
        self.pos = 0.0
        self.tie = False
        self.default_dur = 1
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
        t = self.bar * 4 + self.pos / 4
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

    def parse_bar(self, text):
        text = re.sub(r"%.*", "", text)
        text = re.sub(r"\\clef\s+\"(?:treble|bass)\"", " ", text)
        text = text.replace("~", " ~ ")
        i = 0
        s = text.strip()
        while s:
            s = s.lstrip()
            if not s:
                break
            if s[0] == "~":
                self.tie = True
                s = s[1:]
                continue
            if s[0] == "[":
                end = s.index("]")
                self.parse_group(s[1:end])
                s = s[end + 1:]
                continue
            mr = re.match(r"^r(\d+)(\.?)", s)
            if mr:
                self.emit(0, dur_to_16(int(mr.group(1)), mr.group(2) == "."), True)
                s = s[mr.end():]
                continue
            if s[0] == "r" and (len(s) == 1 or not s[1].isdigit()):
                self.emit(0, self.default_dur, True)
                s = s[1:]
                continue
            mn = re.match(r"^([a-gA-G](?:is|es)?[,']*|[a-z]+[,']*)", s)
            if mn:
                tok = mn.group(1)
                rest = s[mn.end():]
                md = re.match(r"^(\d+)(\.?)", rest)
                if md:
                    d = dur_to_16(int(md.group(1)), md.group(2) == ".")
                    s = s[mn.end() + md.end():]
                else:
                    d = self.default_dur
                    s = s[mn.end():]
                midi = relative_midi(tok, self.last_midi, self.first_midi)
                self.emit(midi, d)
                continue
            md = re.match(r"^(\d+)(\.?)", s)
            if md:
                self.default_dur = dur_to_16(int(md.group(1)), md.group(2) == ".")
                s = s[md.end():]
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
            midi = relative_midi(p, self.last_midi, self.first_midi)
            self.emit(midi, self.default_dur)


def main():
    rh = VoiceParser(VOICEONE, 72, "rh").events   # C5
    lh = VoiceParser(VOICETWO, 48, "lh").events   # C3
    all_ev = sorted(rh + lh, key=lambda e: (e["t"], e["midi"]))
    end = max(e["t"] + e["dur"] for e in all_ev)
    print(f"RH {len(rh)} LH {len(lh)} total {len(all_ev)} end={end:.2f} beats")
    with open("d:/BACH/score772.json", "w", encoding="utf-8") as f:
        json.dump(all_ev, f, separators=(",", ":"))
    with open("d:/BACH/score.json", "w", encoding="utf-8") as f:
        json.dump(all_ev, f, separators=(",", ":"))
    with open("d:/BACH/score.js", "w", encoding="utf-8") as f:
        f.write("const SCORE=" + json.dumps(all_ev, separators=(",", ":")) + ";\n")
    print("RH bar1:", [(round(e["t"], 2), e["midi"]) for e in rh[:12]])


if __name__ == "__main__":
    main()
