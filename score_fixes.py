#!/usr/bin/env python3
"""Bar 6/12/14 RH last-beat sextuplet fixes (silent duplicate). Survives expand/apply pipeline."""


def make_silent_sextuplet(bar_i, voice, remove_ids, pitches, silent_index, t0=3.0):
    """6 notes in 1 beat from t0; one duplicate pitch silent (vel=0)."""
    bs = bar_i * 4
    vel_base = 0.72 if voice == "rh" else 0.52
    # one beat = 1.0; six equal slots
    step = 1.0 / 6
    events = []
    for i, midi in enumerate(pitches):
        events.append({
            "id": f"{voice}-fix{bar_i + 1}-n{i}",
            "t": round(bs + t0 + i * step, 6),
            "dur": round(step * 0.92, 6),
            "midi": midi,
            "vel": 0 if i == silent_index else vel_base,
        })
    return remove_ids, events


def apply_score_fixes(score):
    fixes = [
        # bar 6 RH: bcbag → bcbbag, 4th (=2nd B) silent
        make_silent_sextuplet(
            5, "rh",
            ["rh-88", "rh-89", "rh-90", "rh-91", "rh-92", "rh-93"],
            [83, 84, 83, 83, 81, 79], 3,
        ),
        # bar 12 RH: cdccba, 4th (=2nd C) silent
        make_silent_sextuplet(
            11, "rh",
            ["rh-141", "rh-142", "rh-143"],
            [84, 86, 84, 84, 83, 81], 3,
        ),
        # bar 14 RH: C B A → CDCCBA from first C @ 3.0, 4th C silent
        make_silent_sextuplet(
            13, "rh",
            ["rh-171", "rh-172", "rh-173"],
            [84, 86, 84, 84, 83, 81], 3,
        ),
    ]
    remove_all = set()
    insert_all = []
    for remove_ids, new_ev in fixes:
        remove_all.update(remove_ids)
        insert_all.extend(new_ev)
    out = [e for e in score if e["id"] not in remove_all]
    out.extend(insert_all)
    out.sort(key=lambda e: (e["t"], e["midi"]))
    return out
