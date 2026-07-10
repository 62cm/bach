#!/usr/bin/env python3
"""Render BWV 772a loop audio for HTML5 autoplay (intro silence + score loop)."""
import json
import subprocess
import wave
from pathlib import Path

import numpy as np

BPM = 72
BEAT = 60 / BPM
TOTAL_BARS = 22
PIECE_BEATS = TOTAL_BARS * 4
PIECE_DUR = PIECE_BEATS * BEAT
START_BEAT = (TOTAL_BARS - 1) * 4
INTRO_SEC = (PIECE_BEATS - START_BEAT) * BEAT
SR = 44100
MASTER = 0.18


def subject_vel_mult(n: int) -> float:
    if n <= 3:
        return 1 + (3 - n) * 0.35
    return max(0.12, 1 - (n - 3) * (0.82 / 7))


def midi_freq(m: int) -> float:
    return 440 * (2 ** ((m - 69) / 12))


def triangle(phase: np.ndarray) -> np.ndarray:
    return 2 * np.abs(2 * phase - 1) - 1


def render_buffer(score, tags) -> np.ndarray:
    total_sec = INTRO_SEC + PIECE_DUR
    n = int(total_sec * SR) + SR
    buf = np.zeros(n, dtype=np.float64)

    for ev in score:
        if ev["vel"] <= 0:
            continue
        vel = ev["vel"]
        num = tags.get(ev["id"], 0)
        if 1 <= num <= 10:
            vel *= subject_vel_mult(num)
        peak = min(1.2, max(0.001, vel)) * 0.9 * MASTER

        t0 = INTRO_SEC + ev["t"] * BEAT
        dur = max(0.04, ev["dur"] * BEAT)
        freq = midi_freq(ev["midi"])

        i0 = int(t0 * SR)
        i1 = min(n, i0 + int((dur + 0.03) * SR))
        if i0 >= n or i1 <= i0:
            continue

        length = i1 - i0
        t = np.arange(length, dtype=np.float64) / SR
        phase = (freq * t) % 1.0
        tri = triangle(phase)

        env = np.exp(-np.linspace(0, 4.5, length))
        atk = min(length, max(1, int(0.01 * SR)))
        env[:atk] *= np.linspace(0.05, 1.0, atk)

        buf[i0:i1] += tri * env * peak

    mx = float(np.max(np.abs(buf))) or 1.0
    return (buf / mx * 0.95).astype(np.float32)


def write_wav(path: Path, samples: np.ndarray) -> None:
    pcm = np.clip(samples, -1.0, 1.0)
    pcm16 = (pcm * 32767).astype(np.int16)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm16.tobytes())


def write_m4a(wav_path: Path, m4a_path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(wav_path),
            "-c:a",
            "aac",
            "-b:a",
            "96k",
            "-movflags",
            "+faststart",
            str(m4a_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> None:
    root = Path(__file__).resolve().parent
    score = json.loads((root / "score772_triplet.json").read_text(encoding="utf-8"))
    tags = json.loads((root / "subject_map.json").read_text(encoding="utf-8"))["tags"]
    buf = render_buffer(score, tags)

    wav_path = root / "bwv772a.wav"
    m4a_path = root / "bwv772a.m4a"
    write_wav(wav_path, buf)
    write_m4a(wav_path, m4a_path)

    print(
        f"wrote {m4a_path.name} ({m4a_path.stat().st_size // 1024} KB) "
        f"+ {wav_path.name} | intro={INTRO_SEC:.2f}s loop={PIECE_DUR:.2f}s"
    )


if __name__ == "__main__":
    main()
