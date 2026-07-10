#!/usr/bin/env python3
"""Build BWV 772a lilypond from Mutopia BWV 772 (triplet autograph rhythm)."""
import re

VOICE772_RH = r"""r16 c[ d e] f[ d e c] g'8[ c b c] |
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

VOICE772_LH = r"""r2 r16 c[ d e] f[ d e c] |
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


def norm_pitch(tok: str) -> str:
    tok = tok.strip()
    tok = re.sub(r"\d+\.?$", "", tok)
    return tok + "8"


def beam_to_triplet(head: str, inner: list[str]) -> str:
    notes = [norm_pitch(head)] + [norm_pitch(n) for n in inner]
    if len(notes) == 4:
        # f d e c  →  f e d  (772a manuscript fill)
        notes = [notes[0], notes[2], notes[1]]
    body = " ".join(notes[:3])
    return rf"\tuplet 3/2 {{ {body} }}"


def eighth_beam_to_triplet_plus(head: str, inner: list[str]) -> str:
    """g'8[ c b c]  →  \\tuplet { c b c } g8"""
    tri = beam_to_triplet(inner[0], inner[1:]) if len(inner) >= 3 else ""
    if len(inner) >= 3:
        tnotes = " ".join(norm_pitch(n) for n in inner[:3])
        tri = rf"\tuplet 3/2 {{ {tnotes} }}"
        tail = norm_pitch(head)
        return f"{tri} {tail}"
    return beam_to_triplet(head, inner)


def tripletize_bar(bar: str) -> str:
    s = bar.strip()
    # 休止符时值不动：RH r16、LH r2+r16 保持原样
    out = []
    i = 0
    while i < len(s):
        m = re.match(r"\s+", s[i:])
        if m:
            i += m.end()
            continue
        if s[i:].startswith("~"):
            out.append("~")
            i += 1
            continue
        mr = re.match(r"r(\d+)(\.?)", s[i:])
        if mr:
            out.append(mr.group(0))
            i += mr.end()
            continue
        mn = re.match(r"([a-gA-G](?:is|es)?[,']*)(\d+)(\.?)", s[i:])
        if mn:
            head, num, dot = mn.group(1), int(mn.group(2)), mn.group(3)
            i += mn.end()
            if i < len(s) and s[i] == "[":
                end = s.index("]", i)
                inner = re.findall(r"[a-gA-G](?:is|es)?[,']*", s[i + 1 : end])
                i = end + 1
                if num == 8:
                    out.append(eighth_beam_to_triplet_plus(head + "8" + dot, inner))
                else:
                    out.append(beam_to_triplet(head + str(num) + dot, inner))
                continue
            dur = f"{num}{dot}"
            out.append(f"{head}{dur}")
            continue
        mn2 = re.match(r"([a-gA-G](?:is|es)?[,']*)\[", s[i:])
        if mn2:
            head = mn2.group(1)
            end = s.index("]", i)
            inner = re.findall(r"[a-gA-G](?:is|es)?[,']*", s[i + 1 : end])
            i = end + 1
            out.append(beam_to_triplet(head, inner))
            continue
        out.append(s[i])
        i += 1

    result = " ".join(out)
    result = re.sub(r"\s+", " ", result).strip()
    return result


def convert_voice(text: str) -> str:
    bars = [b.strip() for b in text.strip().split("|") if b.strip()]
    return " |\n".join(tripletize_bar(b) for b in bars) + " |"


def main():
    rh = convert_voice(VOICE772_RH)
    lh = convert_voice(VOICE772_LH)
    ly = f"""% BWV 772a — triplet version (from Mutopia 772, NBA/ABRSM rhythm)
\\version "2.24"
\\include "english.ly"

voiceone = \\relative c' {{
{rh}
}}

voicetwo = \\relative c {{
{lh}
}}
"""
    with open("d:/BACH/bwv772a.ly", "w", encoding="utf-8") as f:
        f.write(ly)
    print("Wrote bwv772a.ly")
    print("Bar1 RH:", rh.split("|")[0].strip())


if __name__ == "__main__":
    main()
