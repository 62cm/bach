#!/usr/bin/env python3
"""Round 1: graphical triplet marking on real BWV 772 score (score772.json)."""
import json

NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
REAL_BEATS = 4


def pname(m):
    return f"{NAMES[m % 12]}{m // 12 - 1}"


def main():
    score = json.load(open("d:/BACH/score772.json", encoding="utf-8"))
    bars = []
    for mb in range(22):
        bs = mb * REAL_BEATS
        row = {"bar": mb + 1, "rh": [], "lh": []}
        for ev in score:
            if bs <= ev["t"] < bs + REAL_BEATS:
                item = {
                    "id": ev["id"],
                    "beat": round(ev["t"] - bs, 4),
                    "midi": ev["midi"],
                    "name": pname(ev["midi"]),
                    "dur": ev["dur"],
                }
                (row["rh"] if ev["id"].startswith("rh") else row["lh"]).append(item)
        bars.append(row)

    data = json.dumps(bars, ensure_ascii=False)
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<title>BWV 772 — 第一轮：标注三连音</title>
<style>
* {{ box-sizing: border-box; }}
body {{ margin: 0; font: 13px/1.35 system-ui, sans-serif; background: #121212; color: #e8e8e8; }}
header {{ padding: 12px 16px; background: #1e1e1e; border-bottom: 1px solid #333; position: sticky; top: 0; z-index: 2; }}
h1 {{ margin: 0 0 6px; font-size: 17px; }}
.legend {{ color: #aaa; max-width: 920px; }}
.legend b {{ color: #8cf; }}
#toolbar {{ margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }}
button {{ padding: 6px 12px; cursor: pointer; border: 1px solid #555; background: #2a2a2a; color: #eee; border-radius: 4px; }}
button.primary {{ border-color: #6a9; background: #1a3a2a; }}
.bar-block {{ margin: 16px; padding: 12px; background: #1a1a1a; border: 1px solid #333; border-radius: 8px; }}
.bar-block h2 {{ margin: 0 0 8px; font-size: 15px; }}
canvas {{ display: block; width: 100%; max-width: 920px; height: auto; cursor: crosshair; background: #0d0d0d; border-radius: 4px; }}
.hint {{ color: #888; font-size: 12px; margin-top: 6px; }}
.group-list {{ margin-top: 8px; color: #aaa; font-size: 12px; }}
</style>
</head>
<body>
<header>
<h1>BWV 772 — 第一轮：标注三连音</h1>
<div class="legend">
<b>谱源：</b>jsbach.net BWV 772 MIDI（David Grossman，1997）— 左右手对齐、时值准确。<br/>
<b>操作：</b>在同一声部里点选属于同一组三连音的音符（如 F 和 D），点「完成此组」。<br/>
<b>处理规则：</b>每组拆成 3 个音 — 音高线性插值（F…D → F E D），时间在组内均分。<br/>
标完导出 <code>triplet_map.json</code>，再运行 <code>python expand_triplets.py</code>。<br/>
<b>注意：</b>每声部每小节只标 <b>2 组</b>（= 两个三连音 = 一个六连音）。多标了 4 组会取 3.0 侧那一对。
</div>
<div id="toolbar">
<button id="finish" class="primary">完成此组</button>
<button id="save">导出 triplet_map.json</button>
<button id="undo">撤销</button>
<button id="clear">清除全部</button>
<span id="status">点选音符加入当前组</span>
</div>
<div id="groups" class="group-list"></div>
</header>
<div id="root"></div>
<script>
const BARS = {data};
const groups = [];
let pending = new Set();
const history = [];

const COLORS = ["#ffb040", "#40c0ff", "#c060ff", "#60ff90", "#ff6080", "#ffd060"];

function groupOf(id) {{
  for (let i = 0; i < groups.length; i++) if (groups[i].ids.includes(id)) return i;
  return -1;
}}

function updateGroups() {{
  const el = document.getElementById("groups");
  if (!groups.length) {{ el.textContent = "尚无三连音组"; return; }}
  el.innerHTML = groups.map((g, i) =>
    `<span style="color:${{COLORS[i % COLORS.length]}}">组${{i+1}}: ${{g.ids.join(", ")}}</span>`
  ).join(" · ");
}}

function updateStatus(msg) {{
  document.getElementById("status").textContent =
    (msg || "") + ` · 当前组 ${{pending.size}} 个音 · 共 ${{groups.length}} 组`;
}}

const NOTE_H = 14;
const BEAT_W = 48;
const LANE_H = 130;
const PAD_L = 44;
const PAD_T = 22;

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
  const notes = row.rh.concat(row.lh);
  const [lo, hi] = midiRange(notes);
  const W = PAD_L + BEAT_W * 4 + 20;
  const H = LANE_H;
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#0d0d0d";
  ctx.fillRect(0, 0, W, H);

  for (let b = 0; b <= 4; b++) {{
    const x = PAD_L + b * BEAT_W;
    ctx.strokeStyle = "#333";
    ctx.setLineDash([]);
    ctx.beginPath(); ctx.moveTo(x, PAD_T); ctx.lineTo(x, H); ctx.stroke();
    if (b < 4) {{
      ctx.fillStyle = "#555"; ctx.font = "10px system-ui";
      ctx.fillText(String(b + 1), x + 3, 12);
    }}
  }}

  ctx.fillStyle = "#888"; ctx.font = "11px system-ui";
  ctx.fillText("RH", 6, PAD_T + 14);
  ctx.fillText("LH", 6, PAD_T + 58);

  function drawVoice(voice, yOff) {{
    for (const n of row[voice]) {{
      const x = PAD_L + n.beat * BEAT_W;
      const y = yForMidi(n.midi, lo, hi, H) + yOff;
      const w = Math.max(8, n.dur * BEAT_W * 0.92);
      const gi = groupOf(n.id);
      const sel = pending.has(n.id);
      ctx.fillStyle = voice === "rh" ? "#c8e0ff" : "#a8d8a8";
      ctx.fillRect(x, y - NOTE_H/2, w, NOTE_H);
      if (gi >= 0) {{
        ctx.strokeStyle = COLORS[gi % COLORS.length];
        ctx.lineWidth = 3;
      }} else if (sel) {{
        ctx.strokeStyle = "#6cf";
        ctx.lineWidth = 2;
      }} else {{
        ctx.strokeStyle = "#555";
        ctx.lineWidth = 1;
      }}
      ctx.strokeRect(x, y - NOTE_H/2, w, NOTE_H);
      ctx.fillStyle = gi >= 0 ? COLORS[gi % COLORS.length] : "#666";
      ctx.font = "9px system-ui";
      ctx.fillText(n.name, x + 2, y - NOTE_H/2 - 2);
    }}
  }}
  drawVoice("rh", 0);
  drawVoice("lh", 4);

  canvas._hits = [];
  for (const v of ["rh", "lh"]) {{
    for (const n of row[v]) {{
      const x = PAD_L + n.beat * BEAT_W;
      const y = yForMidi(n.midi, lo, hi, H);
      const w = Math.max(8, n.dur * BEAT_W * 0.92);
      canvas._hits.push({{ id: n.id, bar: row.bar, voice: v, x, y, w, h: NOTE_H, n }});
    }}
  }}
}}

function render() {{
  const root = document.getElementById("root");
  root.innerHTML = "";
  for (const row of BARS) {{
    const block = document.createElement("div");
    block.className = "bar-block";
    block.innerHTML = `<h2>谱小节 ${{row.bar}}</h2>`;
    const cv = document.createElement("canvas");
    block.appendChild(cv);
    const hint = document.createElement("div");
    hint.className = "hint";
    hint.textContent = "左键点选/取消 · 右键从组中移除";
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
          const gi = groupOf(h.id);
          if (gi >= 0) {{
            groups[gi].ids = groups[gi].ids.filter(x => x !== h.id);
            if (!groups[gi].ids.length) groups.splice(gi, 1);
            updateGroups(); updateStatus(`${{h.n.name}} 移出组`); render(); return;
          }}
          pending.delete(h.id);
          updateStatus(`${{h.n.name}} 取消选择`); render(); return;
        }}
      }}
    }};
    cv.onclick = (e) => {{
      const r = cv.getBoundingClientRect();
      const mx = (e.clientX - r.left) * (cv.width / r.width);
      const my = (e.clientY - r.top) * (cv.height / r.height);
      for (const h of cv._hits) {{
        if (mx >= h.x && mx <= h.x + h.w && my >= h.y - h.h/2 && my <= h.y + h.h/2) {{
          if (groupOf(h.id) >= 0) {{ updateStatus(`${{h.n.name}} 已在某组里`); return; }}
          if (pending.has(h.id)) pending.delete(h.id);
          else pending.add(h.id);
          updateStatus(`${{h.n.name}} ${{pending.has(h.id) ? "加入" : "移出"}}`); render(); return;
        }}
      }}
    }};
  }}
  updateGroups();
}}

document.getElementById("finish").onclick = () => {{
  if (pending.size < 2) {{ updateStatus("至少选 2 个音"); return; }}
  const ids = [...pending];
  groups.push({{ ids }});
  history.push({{ type: "group", ids: [...ids] }});
  pending.clear();
  updateStatus("组已保存"); render();
}};

document.getElementById("save").onclick = () => {{
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify({{ groups }}, null, 2)], {{type: "application/json"}}));
  a.download = "triplet_map.json"; a.click();
}};

document.getElementById("undo").onclick = () => {{
  const last = history.pop();
  if (!last) return;
  if (last.type === "group") {{
    groups.pop();
    updateStatus("撤销上一组"); render();
  }}
}};

document.getElementById("clear").onclick = () => {{
  groups.length = 0; pending.clear(); history.length = 0;
  updateStatus("已清除"); render();
}};

render();
</script>
</body>
</html>"""
    with open("d:/BACH/triplet_graph.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Wrote triplet_graph.html (from score772.json)")


if __name__ == "__main__":
    main()
