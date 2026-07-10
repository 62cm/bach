#!/usr/bin/env python3
"""Embed score.json into index.html."""
import json
import re
import subprocess
import sys

def main():
    subprocess.run([sys.executable, "d:/BACH/build_score.py"], check=True)
    raw = json.load(open("d:/BACH/score.json", encoding="utf-8"))
    score_js = "const SCORE=" + json.dumps(raw, separators=(",", ":")) + ";"
    path = "d:/BACH/index.html"
    html = open(path, encoding="utf-8").read()
    block = f"<script>\n{score_js}\n</script>"
    html = re.sub(r"<script>\s*const SCORE=[\s\S]*?</script>", block, html, count=1)
    open(path, "w", encoding="utf-8").write(html)
    open("d:/BACH/score.js", "w", encoding="utf-8").write(score_js + "\n")
    print(f"embedded {len(raw)} events, 4/4, {max(e['t'] for e in raw)/4:.0f} bars")


if __name__ == "__main__":
    main()
