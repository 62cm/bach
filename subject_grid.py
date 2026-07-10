#!/usr/bin/env python3
"""772a 主题拍点：每组三连音 = 1 个八分音符，10 在第 5 格（2.0 拍）。"""
EIGHTH = 0.5
STEP = EIGHTH / 3

SUBJECT_ONSETS = {
    1: 0,
    2: STEP,
    3: 2 * STEP,
    4: EIGHTH,
    5: EIGHTH + STEP,
    6: EIGHTH + 2 * STEP,
    7: 2 * EIGHTH,
    8: 2 * EIGHTH + STEP,
    9: 2 * EIGHTH + 2 * STEP,
    10: 4 * EIGHTH,  # 2.0 拍 = 网格第 5 线
}

VOICE_BASE = {"rh": 0.0, "lh": 2.25}  # LH 在 RH 第 10 音 + r16 后进入
NOTE10_BEAT = {"rh": 2.0, "lh": 4.0}

DUR_TRIP = round(EIGHTH / 3 * 0.92, 6)
DUR_10 = round(EIGHTH * 0.85, 6)


def voice_of(eid):
    return "rh" if eid.startswith("rh") else "lh"


def subject_beat(num, voice):
    if num == 10:
        return NOTE10_BEAT[voice]
    return VOICE_BASE[voice] + SUBJECT_ONSETS[num]


def retime_subject(score, tags):
    """把已标注 1–10 的音符对齐到固定主题网格（保留音高）。"""
    by_id = {e["id"]: e for e in score}
    skip = set()
    out = []

    for eid, num in tags.items():
        if eid not in by_id or not (1 <= num <= 10):
            continue
        ev = by_id[eid]
        bar = int(ev["t"] // 4)
        voice = voice_of(eid)
        t = round(bar * 4 + subject_beat(num, voice), 6)
        dur = DUR_10 if num == 10 else DUR_TRIP
        out.append({**ev, "t": t, "dur": dur})
        skip.add(eid)

    for ev in score:
        if ev["id"] not in skip:
            out.append(ev)
    out.sort(key=lambda e: (e["t"], e["midi"]))
    return out
