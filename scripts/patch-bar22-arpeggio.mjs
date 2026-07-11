#!/usr/bin/env node
/** Bar 22 ending: spread 16th-note arpeggio low → high (was 32nd blur). */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, "..");

const BAR_START = 84;
const PIECE_END = 88;
const ARP_STEP = 0.25; // 16th note

const BAR22_IDS = ["lh-219", "lh-218", "rh-253", "rh-252", "rh-251"];

function patchScore(score) {
  const notes = BAR22_IDS.map((id) => score.find((e) => e.id === id)).filter(Boolean);
  if (notes.length !== BAR22_IDS.length) {
    throw new Error(`bar 22 notes missing: got ${notes.length}`);
  }
  notes.sort((a, b) => a.midi - b.midi);
  notes.forEach((n, i) => {
    n.t = round6(BAR_START + i * ARP_STEP);
    n.dur = round6(PIECE_END - n.t - 0.02);
  });
  score.sort((a, b) => a.t - b.t || a.midi - b.midi);
  return score;
}

function round6(x) {
  return Math.round(x * 1e6) / 1e6;
}

function embedHtml(file) {
  const score = JSON.parse(fs.readFileSync(path.join(ROOT, "score772_triplet.json"), "utf8"));
  const raw = fs.readFileSync(file, "utf8");
  const scoreJs = "const SCORE=" + JSON.stringify(score) + ";";
  return raw.replace(/const SCORE=\[[\s\S]*?\];/, scoreJs);
}

function main() {
  for (const name of ["score772_triplet.json", "score772.json"]) {
    const p = path.join(ROOT, name);
    const score = JSON.parse(fs.readFileSync(p, "utf8"));
    patchScore(score);
    fs.writeFileSync(p, JSON.stringify(score));
    console.log("patched", name);
  }

  const score = JSON.parse(fs.readFileSync(path.join(ROOT, "score772_triplet.json"), "utf8"));
  const scoreJs =
    "const SCORE=" + JSON.stringify(score) + ";\n" + fs.readFileSync(path.join(ROOT, "score.js"), "utf8").replace(/^const SCORE=\[[\s\S]*?\];\n?/, "");
  fs.writeFileSync(path.join(ROOT, "score.js"), scoreJs);

  for (const html of ["BWV772a.html", "index.html"]) {
    fs.writeFileSync(path.join(ROOT, html), embedHtml(path.join(ROOT, html)));
    console.log("embedded", html);
  }
}

main();
