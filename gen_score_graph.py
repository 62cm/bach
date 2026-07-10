#!/usr/bin/env python3
"""Generate score_graph.html — one 4-beat piano-roll per notated measure."""
import json

NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
REAL_BEATS = 4
MEASURE_KIND = [
    "subject", "subject", "subject", "flat",
    "subject", "subject", "flat",
    "subject", "subject", "subject", "flat",
    "subject", "subject", "flat",
    "subject", "subject", "flat",
    "subject", "subject", "flat",
    "subject", "flat",
]

def pname(m):
    return f"{NAMES[m % 12]}{m // 12 - 1}"


def main():
    import os
    base = "d:/BACH/score772_triplet.json" if os.path.isfile("d:/BACH/score772_triplet.json") else "d:/BACH/score772.json"
    score = json.load(open(base, encoding="utf-8"))
    bars = []
    for mb in range(22):
        bs = mb * REAL_BEATS
        row = {
            "bar": mb + 1,
            "step": MEASURE_KIND[mb],
            "subject": MEASURE_KIND[mb] == "subject",
            "rh": [],
            "lh": [],
            "spill_rh": [],
            "spill_lh": [],
        }
        for ev in score:
            t = ev["t"]
            if bs <= t < bs + REAL_BEATS:
                item = {
                    "id": ev["id"],
                    "beat": round(t - bs, 4),
                    "midi": ev["midi"],
                    "name": pname(ev["midi"]),
                    "dur": ev["dur"],
                    "vel": ev.get("vel", 0.72),
                }
                (row["rh"] if ev["id"].startswith("rh") else row["lh"]).append(item)
            elif row["subject"] and mb < 21:
                nbs = (mb + 1) * REAL_BEATS
                if nbs <= t < nbs + 1.0:
                    item = {
                        "id": ev["id"],
                        "beat": round(t - bs, 4),
                        "midi": ev["midi"],
                        "name": pname(ev["midi"]),
                        "dur": ev["dur"],
                        "vel": ev.get("vel", 0.72),
                        "spill": True,
                    }
                    (row["spill_rh"] if ev["id"].startswith("rh") else row["spill_lh"]).append(item)
        bars.append(row)

    data = json.dumps(bars, ensure_ascii=False)
    preset_tags = "{}"
    if os.path.isfile("d:/BACH/subject_map.json"):
        preset_tags = json.dumps(
            json.load(open("d:/BACH/subject_map.json", encoding="utf-8")).get("tags", {}),
            ensure_ascii=False,
        )
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<title>BWV 772a 图形标注</title>
<style>
* {{ box-sizing: border-box; }}
body {{ margin: 0; font: 13px/1.35 system-ui, sans-serif; background: #121212; color: #e8e8e8; }}
header {{ padding: 12px 16px; background: #1e1e1e; border-bottom: 1px solid #333; position: sticky; top: 0; z-index: 2; }}
h1 {{ margin: 0 0 6px; font-size: 17px; }}
.legend {{ color: #aaa; max-width: 920px; }}
.legend b {{ color: #8cf; }}
#toolbar {{ margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }}
#numPad {{ display: flex; gap: 4px; flex-wrap: wrap; }}
#numPad button {{
  min-width: 36px; padding: 8px 10px; font-weight: bold; font-size: 14px;
}}
#numPad button.active {{ background: #ffb040; color: #111; border-color: #ffb040; }}
button {{ padding: 6px 12px; cursor: pointer; border: 1px solid #555; background: #2a2a2a; color: #eee; border-radius: 4px; }}
.bar-block {{ margin: 16px; padding: 12px; background: #1a1a1a; border: 1px solid #333; border-radius: 8px; }}
.bar-block.subject {{ border-color: #4a7ab8; }}
.bar-block h2 {{ margin: 0 0 8px; font-size: 15px; }}
.bar-block h2 .tag {{ color: #8cf; font-weight: normal; }}
canvas {{ display: block; width: 100%; max-width: 920px; height: auto; cursor: crosshair; background: #0d0d0d; border-radius: 4px; }}
.hint {{ color: #888; font-size: 12px; margin-top: 6px; }}
</style>
</head>
<body>
<header>
<h1>BWV 772 — 主题 1–10 手动标注</h1>
<div class="legend">
<b>标尺：</b>每小节固定 <b>8 格</b>，每格 = <b>1 个八分音符</b>（4/4 小节共 8 个八分音）。虚线不动，音符按 MIDI 时间画。<br/>
<b>第 10 音</b> 可能在下一小节 — 主题小节右侧灰色区是<strong>下小节第 1 拍</strong>，也可点选。<br/>
<b>说明：</b>左右手各自可标 1–10，同一小节里 RH 和 LH 可以有相同数字。
</div>
<div id="toolbar">
<div id="numPad"></div>
<button id="save">导出 subject_map.json</button>
<button id="undo">撤销</button>
<button id="clear">清除全部</button>
<span id="status">当前选中：<b>1</b></span>
</div>
</header>
<div id="root"></div>
<script>
const BARS = {data};
const tags = {preset_tags};
const history = [];
let selectedNum = 1;

function updateNumPad() {{
  const pad = document.getElementById("numPad");
  pad.innerHTML = "";
  for (let i = 1; i <= 10; i++) {{
    const b = document.createElement("button");
    b.textContent = String(i);
    b.className = i === selectedNum ? "active" : "";
    b.onclick = () => {{ selectedNum = i; updateNumPad(); updateStatus(); }};
    pad.appendChild(b);
  }}
}}

function updateStatus(msg) {{
  document.getElementById("status").innerHTML =
    (msg ? msg + " · " : "") + `当前选中：<b>${{selectedNum}}</b>`;
}}

const NOTE_H = 14;
const BEAT_W = 48;
const LANE_H = 130;
const PAD_L = 44;
const PAD_T = 22;
const SPILL_BEATS = 1;

function barWidth(row) {{
  return PAD_L + BEAT_W * (row.subject && row.bar < 22 ? 4 + SPILL_BEATS : 4) + 20;
}}

function allNotes(row) {{
  return row.rh.concat(row.lh, row.spill_rh || [], row.spill_lh || []);
}}

function midiRange(notes) {{
  if (!notes.length) return [48, 84];
  let lo = 999, hi = 0;
  for (const n of notes) {{ lo = Math.min(lo, n.midi); hi = Math.max(hi, n.midi); }}
  return [lo - 2, hi + 2];
}}

function yForMidi(midi, lo, hi, h) {{
  return PAD_T + (1 - (midi - lo) / Math.max(1, hi - lo)) * (h - PAD_T - 10);
}}

function drawBar(row, canvas) {{
  const notes = allNotes(row);
  const [lo, hi] = midiRange(notes);
  const beats = row.subject && row.bar < 22 ? 4 + SPILL_BEATS : 4;
  const W = PAD_L + BEAT_W * beats + 20;
  const H = LANE_H;
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#0d0d0d";
  ctx.fillRect(0, 0, W, H);

  if (beats > 4) {{
    ctx.fillStyle = "rgba(80,80,80,0.15)";
    ctx.fillRect(PAD_L + 4 * BEAT_W, PAD_T, SPILL_BEATS * BEAT_W, H - PAD_T);
    ctx.fillStyle = "#666"; ctx.font = "10px system-ui";
    ctx.fillText("下小节", PAD_L + 4 * BEAT_W + 4, 12);
  }}

  // 8 格 = 8 个八分音符（每格 0.5 拍）
  const eighths = Math.round(beats * 2);
  for (let i = 0; i <= eighths; i++) {{
    const beat = i * 0.5;
    const x = PAD_L + beat * BEAT_W;
    const isBarEnd = i === 8;
    const isHalf = i === 4;
    ctx.strokeStyle = isBarEnd && beats > 4 ? "#444" : isHalf ? "#333" : "#252525";
    ctx.setLineDash(isBarEnd && beats > 4 ? [4, 4] : isHalf ? [6, 4] : []);
    ctx.beginPath(); ctx.moveTo(x, PAD_T); ctx.lineTo(x, H); ctx.stroke();
    ctx.setLineDash([]);
    if (i < 8) {{
      ctx.fillStyle = "#555"; ctx.font = "10px system-ui";
      ctx.fillText(String(i + 1), x + 2, 12);
    }}
  }}

  ctx.fillStyle = "rgba(90,142,200,0.06)";
  ctx.fillRect(PAD_L, PAD_T, 0.25 * BEAT_W, H - PAD_T);

  ctx.fillStyle = "#888"; ctx.font = "11px system-ui";
  ctx.fillText("RH", 6, PAD_T + 14);
  ctx.fillText("LH", 6, PAD_T + 58);

  function drawVoice(list, yOff, voice) {{
    for (const n of list) {{
      const x = PAD_L + n.beat * BEAT_W;
      const y = yForMidi(n.midi, lo, hi, H) + yOff;
      const w = Math.max(8, n.dur * BEAT_W * 0.92);
      const tag = tags[n.id] || 0;
      ctx.fillStyle = voice === "rh" ? "#c8e0ff" : "#a8d8a8";
      if (n.vel === 0) ctx.fillStyle = voice === "rh" ? "#3a4a5a" : "#3a5a4a";
      if (n.spill) ctx.globalAlpha = 0.85;
      ctx.fillRect(x, y - NOTE_H/2, w, NOTE_H);
      ctx.globalAlpha = 1;
      ctx.strokeStyle = tag ? "#ffb040" : (n.spill ? "#777" : "#555");
      ctx.lineWidth = tag ? 2 : 1;
      ctx.strokeRect(x, y - NOTE_H/2, w, NOTE_H);
      if (tag) {{
        ctx.fillStyle = "#ffb040"; ctx.font = "bold 11px system-ui";
        ctx.fillText(String(tag), x + 3, y + 4);
      }}
      ctx.fillStyle = n.spill ? "#888" : "#666"; ctx.font = "9px system-ui";
      ctx.fillText(n.name, x + 2, y - NOTE_H/2 - 2);
    }}
  }}
  drawVoice(row.rh, 0, "rh");
  drawVoice(row.lh, 4, "lh");
  drawVoice(row.spill_rh || [], 0, "rh");
  drawVoice(row.spill_lh || [], 4, "lh");

  canvas._hits = [];
  for (const list of [row.rh, row.lh, row.spill_rh || [], row.spill_lh || []]) {{
    for (const n of list) {{
      const x = PAD_L + n.beat * BEAT_W;
      const y = yForMidi(n.midi, lo, hi, H);
      const w = Math.max(8, n.dur * BEAT_W * 0.92);
      canvas._hits.push({{ id: n.id, bar: row.bar, x, y, w, h: NOTE_H, n }});
    }}
  }}
}}

function render() {{
  const root = document.getElementById("root");
  root.innerHTML = "";
  for (const row of BARS) {{
    const block = document.createElement("div");
    block.className = "bar-block" + (row.subject ? " subject" : "");
    block.innerHTML = `<h2>谱小节 ${{row.bar}} <span class="tag">${{row.step}}</span></h2>`;
    const cv = document.createElement("canvas");
    block.appendChild(cv);
    const hint = document.createElement("div");
    hint.className = "hint";
    hint.textContent = row.subject
      ? "点 1–10 按钮 → 点音符；右侧灰区=下小节第1拍（可标第10音）"
      : "非主题小节也可标（若需要）";
    block.appendChild(hint);
    root.appendChild(block);
    drawBar(row, cv);
    cv.oncontextmenu = (e) => {{
      e.preventDefault();
      const r = cv.getBoundingClientRect();
      const mx = (e.clientX - r.left) * (cv.width / r.width);
      const my = (e.clientY - r.top) * (cv.height / r.height);
      for (const h of cv._hits) {{
        if (mx >= h.x && mx <= h.x + h.w && my >= h.y - h.h/2 && my <= h.y + h.h/2) {{
          if (!tags[h.id]) return;
          const rm = tags[h.id]; delete tags[h.id];
          for (let i = history.length - 1; i >= 0; i--) if (history[i].id === h.id) {{ history.splice(i, 1); break; }}
          updateStatus(`${{h.n.name}} 取消 ${{rm}}`); render(); return;
        }}
      }}
    }};
    cv.onclick = (e) => {{
      const r = cv.getBoundingClientRect();
      const mx = (e.clientX - r.left) * (cv.width / r.width);
      const my = (e.clientY - r.top) * (cv.height / r.height);
      for (const h of cv._hits) {{
        if (mx >= h.x && mx <= h.x + h.w && my >= h.y - h.h/2 && my <= h.y + h.h/2) {{
          const prev = tags[h.id];
          if (prev === selectedNum) {{ updateStatus(`${{h.n.name}} 已是 ${{selectedNum}}`); return; }}
          tags[h.id] = selectedNum;
          history.push({{ id: h.id, n: selectedNum, prev: prev || 0 }});
          const where = h.n.spill ? "（下小节）" : "";
          updateStatus(`${{h.n.name}}${{where}} → ${{selectedNum}}`); render(); return;
        }}
      }}
    }};
  }}
}}

document.getElementById("save").onclick = () => {{
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify({{ tags }}, null, 2)], {{type: "application/json"}}));
  a.download = "subject_map.json"; a.click();
}};
document.getElementById("undo").onclick = () => {{
  const last = history.pop(); if (!last) return;
  if (last.prev) tags[last.id] = last.prev;
  else delete tags[last.id];
  updateStatus(`撤销 ${{last.n}}`); render();
}};
document.getElementById("clear").onclick = () => {{
  for (const k of Object.keys(tags)) delete tags[k];
  history.length = 0;
  updateStatus("已清除"); render();
}};
updateNumPad();
render();
</script>
</body>
</html>"""
    with open("d:/BACH/score_graph.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Wrote score_graph.html")


if __name__ == "__main__":
    main()
