#!/usr/bin/env python3
"""Embed score772 into index.html (from MIDI via parse_midi.py)."""
import json
import re
import subprocess
import sys


def main():
    subprocess.run([sys.executable, "d:/BACH/parse_midi.py"], check=True)
    raw = json.load(open("d:/BACH/score772.json", encoding="utf-8"))
    score_js = "const SCORE=" + json.dumps(raw, separators=(",", ":")) + ";"
    path = "d:/BACH/index.html"
    html = open(path, encoding="utf-8").read()
    block = f"<script>\n{score_js}\n</script>"
    if re.search(r"const SCORE=", html):
        html = re.sub(r"<script>\s*const SCORE=[\s\S]*?</script>", block, html, count=1)
    else:
        html = html.replace('<script src="score.js"></script>', block)
    open(path, "w", encoding="utf-8").write(html)
    open("d:/BACH/score.js", "w", encoding="utf-8").write(score_js + "\n")
    print(f"index.html now uses real score772 ({len(raw)} events)")


if __name__ == "__main__":
    main()
