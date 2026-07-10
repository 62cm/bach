#!/usr/bin/env python3
"""Generate score_sheet.html + score_list.txt from real parsed score772."""
import json

NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def pname(m):
    return f"{NAMES[m % 12]}{m // 12 - 1}"


def main():
    score = json.load(open("d:/BACH/score772a.json", encoding="utf-8"))
    steps = [
        "subject", "subject", "subject", "flat",
        "subject", "subject", "flat",
        "subject", "subject", "subject", "flat",
        "subject", "subject", "flat",
        "subject", "subject", "flat",
        "subject", "subject", "flat",
        "subject", "flat",
    ]
    bars = []
    for b in range(22):
        bs = b * 4
        row = {"bar": b + 1, "step": steps[b], "rh": [], "lh": []}
        for ev in score:
            if bs <= ev["t"] < bs + 4:
                beat = round(ev["t"] - bs, 3)
                item = {
                    "id": ev["id"],
                    "beat": beat,
                    "midi": ev["midi"],
                    "name": pname(ev["midi"]),
                    "dur": ev["dur"],
                }
                if ev["id"].startswith("rh"):
                    row["rh"].append(item)
                else:
                    row["lh"].append(item)
        bars.append(row)

    with open("d:/BACH/score_list.txt", "w", encoding="utf-8") as f:
        f.write("BWV 772a 三连音版 — 4/4 一小节4拍\n\n")
        for b in range(22):
            bs = b * 4
            kind = steps[b]
            f.write(f"=== 谱小节 {b+1} ({kind}) ===\n")
            for v in ("rh", "lh"):
                f.write(f"  {v.upper()}:")
                for ev in score:
                    if not ev["id"].startswith(v):
                        continue
                    if bs <= ev["t"] < bs + 4:
                        f.write(f"  [{ev['t']-bs:.2f} {pname(ev['midi'])}]")
                f.write("\n")
            f.write("\n")

    data = json.dumps(bars, ensure_ascii=False)
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<title>772 乐谱标注</title>
<style>
* {{ box-sizing: border-box; }}
body {{ font: 14px/1.4 system-ui, sans-serif; margin: 16px; background: #1a1a1a; color: #ddd; }}
h1 {{ font-size: 18px; }}
.legend {{ background: #2a2a2a; padding: 12px; border-radius: 8px; margin-bottom: 16px; }}
.bar {{ border: 1px solid #444; margin-bottom: 12px; padding: 10px; border-radius: 6px; }}
.bar.subject {{ border-color: #8af; }}
.bar h2 {{ margin: 0 0 8px; font-size: 15px; }}
.bar h2 span {{ color: #8af; font-weight: normal; }}
.voice {{ margin: 6px 0; }}
.note {{ display: inline-block; margin: 3px; padding: 4px 8px; border: 1px solid #555; border-radius: 4px; cursor: pointer; user-select: none; }}
.note.on {{ border-color: #fc8; background: #432; }}
.note .tag {{ color: #fc8; font-weight: bold; margin-left: 4px; }}
#save {{ margin-top: 16px; padding: 10px 20px; font-size: 15px; cursor: pointer; }}
</style>
</head>
<body>
<h1>BWV 772a 三连音版 — 点击音符标注 1–10</h1>
<div class="legend">
<b>十个音：</b> 1·2·3（前三个）→ 4·5·6、7·8·9（两组三连音）→ 10（最后音，滚入下一小节空拍）<br/>
<b>网格拍点：</b> 空 0–0.5 | 1=0.5 2=1.0 3=1.5 | 4=2.0 5=2.33 6=2.67 | 7=3.0 8=3.33 9=3.67 | 10→4.0<br/>
点音符顺序标注：第 1 下=1，第 2 下=2…每小节从 1 数到 10。已标过的音再点无效；右键取消。
</div>
<div id="bars"></div>
<button id="save">导出 subject_map.json</button>
<button id="undo">撤销</button>
<button id="clear">清除</button>
<span id="status"></span>
<script>
const BARS = {data};
const tags = {{}};
const barNext = {{}};
const history = [];

function recalcBarNext(bar) {{
  let max = 0;
  for (const row of BARS) {{
    if (row.bar !== bar) continue;
    for (const v of ["rh", "lh"]) {{
      for (const n of row[v]) if (tags[n.id]) max = Math.max(max, tags[n.id]);
    }}
  }}
  barNext[bar] = max + 1;
}}

function updateStatus(bar, msg) {{
  const n = barNext[bar] || 1;
  document.getElementById("status").textContent =
    (msg || "") + (n <= 10 ? ` · 小节${{bar}} 下一个：${{n}}` : ` · 小节${{bar}} 已满`);
}}

function render() {{
  const root = document.getElementById("bars");
  root.innerHTML = "";
  for (const row of BARS) {{
    const div = document.createElement("div");
    div.className = "bar " + row.step;
    div.innerHTML = `<h2>小节 ${{row.bar}} <span>${{row.step}}</span></h2>`;
    for (const v of ["rh", "lh"]) {{
      const p = document.createElement("div");
      p.className = "voice";
      p.textContent = v.toUpperCase() + ": ";
      for (const n of row[v]) {{
        const b = document.createElement("span");
        b.className = "note";
        b.dataset.id = n.id;
        const t = tags[n.id] || 0;
        if (t) {{ b.classList.add("on"); b.innerHTML = `${{n.beat.toFixed(2)}} ${{n.name}}<span class="tag">${{t}}</span>`; }}
        else {{ b.textContent = `${{n.beat.toFixed(2)}} ${{n.name}}`; }}
        b.onclick = () => {{
          if (tags[n.id]) {{ updateStatus(row.bar, `${{n.name}} 已是 ${{tags[n.id]}}`); return; }}
          recalcBarNext(row.bar);
          const num = barNext[row.bar];
          if (num > 10) {{ updateStatus(row.bar, "已满 10 个"); return; }}
          tags[n.id] = num;
          barNext[row.bar] = num + 1;
          history.push({{ bar: row.bar, id: n.id, n: num }});
          updateStatus(row.bar, `${{n.name}} → ${{num}}`);
          render();
        }};
        b.oncontextmenu = (e) => {{
          e.preventDefault();
          if (!tags[n.id]) return;
          const rm = tags[n.id];
          delete tags[n.id];
          for (let i = history.length - 1; i >= 0; i--) if (history[i].id === n.id) {{ history.splice(i, 1); break; }}
          recalcBarNext(row.bar);
          updateStatus(row.bar, `${{n.name}} 取消 ${{rm}}`);
          render();
        }};
        p.appendChild(b);
      }}
      div.appendChild(p);
    }}
    root.appendChild(div);
  }}
}}
document.getElementById("save").onclick = () => {{
  const blob = new Blob([JSON.stringify({{ tags }}, null, 2)], {{type: "application/json"}});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "subject_map.json";
  a.click();
}};
document.getElementById("undo").onclick = () => {{
  const last = history.pop();
  if (!last) return;
  delete tags[last.id];
  recalcBarNext(last.bar);
  updateStatus(last.bar, `撤销 ${{last.n}}`);
  render();
}};
document.getElementById("clear").onclick = () => {{
  for (const k of Object.keys(tags)) delete tags[k];
  for (const k of Object.keys(barNext)) delete barNext[k];
  history.length = 0;
  document.getElementById("status").textContent = "已清除";
  render();
}};
render();
</script>
</body>
</html>"""
    with open("d:/BACH/score_sheet.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Wrote score_sheet.html + score_list.txt")


if __name__ == "__main__":
    main()
