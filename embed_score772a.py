#!/usr/bin/env python3
"""Embed score772a into index.html."""
import json
import re

def main():
    raw = json.load(open("d:/BACH/score772a.json", encoding="utf-8"))
    score_js = "const SCORE=" + json.dumps(raw, separators=(",", ":")) + ";"
    path = "d:/BACH/index.html"
    html = open(path, encoding="utf-8").read()
    block = f"<script>\n{score_js}\n</script>"
    html = re.sub(r"<script>\s*const SCORE=[\s\S]*?</script>", block, html, count=1)
    open(path, "w", encoding="utf-8").write(html)
    open("d:/BACH/score.js", "w", encoding="utf-8").write(score_js + "\n")
    print(f"index.html now uses BWV 772a ({len(raw)} events)")


if __name__ == "__main__":
    main()
