#!/usr/bin/env node
/**
 * Headless draw verification for BWV772a bar-22 / platform rules.
 * Run: node scripts/verify-bwv772a.mjs
 */
import fs from "fs";
import http from "http";
import path from "path";
import { fileURLToPath } from "url";
import puppeteer from "puppeteer-core";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, "..");
const HTML_PATH = path.join(ROOT, "BWV772a.html");

const INJECT = `
  window.__TEST__ = {
    boot() {
      started = true;
      loopCount = 0;
      prevPlan = -1;
      prevStepIndex = -1;
    },
    setLoop(n) { loopCount = n; },
    getLoop() { return loopCount; },
    runTrack(t0, t1, step) {
      for (let t = t0; t <= t1; t += step) trackLoop(t);
    },
    drawAt(t) {
      trackLoop(t);
      draw(t);
    },
    locate,
    scrollXAt,
    stepScreen,
    isBar22,
    planOf,
    stepKind,
    ballState,
    START_BEAT,
    BEAT,
    PIECE_BEATS,
    N_STEPS,
    INTRO_TOTAL_BEATS,
    REST,
    W,
    H,
    DARK,
    LIGHT,
    ORIGIN_Y,
    STEP_H,
    cumDropUpTo,
    stepWidth,
  };
`;

function buildHtml() {
  const raw = fs.readFileSync(HTML_PATH, "utf8");
  return raw.replace(/\}\)\(\);\s*\n\s*<\/script>/, `${INJECT}\n})();\n  </script>`);
}

function startServer(html) {
  return new Promise((resolve) => {
    const server = http.createServer((_req, res) => {
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      res.end(html);
    });
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address();
      resolve({ server, url: `http://127.0.0.1:${port}/` });
    });
  });
}

function parseColor(hex) {
  const h = hex.replace("#", "");
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}

function colorDist(a, b) {
  return Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]) + Math.abs(a[2] - b[2]);
}

async function samplePage(page) {
  return page.evaluate(() => {
    const canvas = document.getElementById("stage");
    const ctx = canvas.getContext("2d");
    const { width, height } = canvas;
    const data = ctx.getImageData(0, 0, width, height).data;
    const T = window.__TEST__;
    return {
      width,
      height,
      dpr: width / T.W,
      data: Array.from(data),
    };
  });
}

function fgAt(sample, x, y, fg, bg, tol = 40) {
  const dpr = sample.dpr;
  const px = Math.floor(x * dpr);
  const py = Math.floor(y * dpr);
  const i = (py * sample.width + px) * 4;
  const rgb = [sample.data[i], sample.data[i + 1], sample.data[i + 2]];
  const fgC = parseColor(fg);
  const bgC = parseColor(bg);
  return colorDist(rgb, fgC) < colorDist(rgb, bgC) && colorDist(rgb, fgC) <= tol;
}

function lineHasFg(sample, y, x0, x1, fg, bg, minHits = 8) {
  let hits = 0;
  const step = Math.max(1, Math.floor((x1 - x0) / 40));
  for (let x = x0; x <= x1; x += step) {
    if (fgAt(sample, x, y, fg, bg)) hits++;
  }
  return hits >= minHits;
}

function regionFgRatio(sample, x0, y0, x1, y1, fg, bg) {
  let fgN = 0;
  let total = 0;
  for (let y = y0; y <= y1; y += 2) {
    for (let x = x0; x <= x1; x += 2) {
      total++;
      if (fgAt(sample, x, y, fg, bg)) fgN++;
    }
  }
  return total ? fgN / total : 0;
}

async function drawAndSample(page, tMus) {
  await page.evaluate((t) => {
    window.__TEST__.drawAt(t);
  }, tMus);
  return samplePage(page);
}

async function meta(page, tMus) {
  return page.evaluate((t) => {
    const T = window.__TEST__;
    const loc = T.locate(t);
    const scrollX = T.scrollXAt(t);
    const sCur = T.stepScreen(loc.stepIndex, scrollX, t);
    const sPrev = T.stepScreen(loc.stepIndex - 1, scrollX, t);
    const ball = T.ballState(t);
    return {
      tMus: t,
      beat: t / T.BEAT,
      loopCount: T.getLoop(),
      stepIndex: loc.stepIndex,
      plan: loc.plan,
      beatInStep: loc.beatInStep,
      onBar22: T.isBar22(loc.plan),
      sCur,
      sPrev,
      ball,
    };
  }, tMus);
}

async function main() {
  const html = buildHtml();
  const { server, url } = await startServer(html);

  const browser = await puppeteer.launch({
    executablePath: "/usr/local/bin/google-chrome",
    headless: "new",
    args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 520, height: 400, deviceScaleFactor: 1 });
  await page.goto(url, { waitUntil: "networkidle0" });
  await page.evaluate(() => window.__TEST__.boot());

  const T = await page.evaluate(() => {
    const x = window.__TEST__;
    return {
      START_BEAT: x.START_BEAT,
      BEAT: x.BEAT,
      PIECE_BEATS: x.PIECE_BEATS,
      INTRO_TOTAL_BEATS: x.INTRO_TOTAL_BEATS,
      REST: x.REST,
      N_STEPS: x.N_STEPS,
    };
  });

  const failures = [];
  const pass = (name) => console.log(`  PASS  ${name}`);
  const fail = (name, detail) => {
    console.log(`  FAIL  ${name}`);
    console.log(`        ${detail}`);
    failures.push({ name, detail });
  };

  console.log("BWV772a draw verification\n");

  // --- 1. First opening on bar 22 ---
  const tOpen = (T.START_BEAT + T.INTRO_TOTAL_BEATS * 0.5) * T.BEAT;
  const mOpen = await meta(page, tOpen);
  await page.evaluate(() => {
    window.__TEST__.loopCount = 0;
    window.__TEST__.prevPlan = -1;
    window.__TEST__.prevStepIndex = -1;
  });
  const sampleOpen = await drawAndSample(page, tOpen);
  const fgOpen = mOpen.plan % 2 === 1 ? "#0d0d0d" : "#cccccc";
  const bgOpen = mOpen.plan % 2 === 1 ? "#cccccc" : "#0d0d0d";
  const y22 = mOpen.sCur.y;

  if (mOpen.onBar22 && mOpen.loopCount === 0) pass("opening: on bar 22, loopCount 0");
  else fail("opening: on bar 22, loopCount 0", JSON.stringify(mOpen));

  if (lineHasFg(sampleOpen, y22, 0, mOpen.sCur.x + mOpen.sCur.w, fgOpen, bgOpen))
    pass("opening: bar 22 horizontal platform visible");
  else fail("opening: bar 22 horizontal platform visible", `y=${y22} sCur=${JSON.stringify(mOpen.sCur)}`);

  const fragRatio = regionFgRatio(sampleOpen, 0, mOpen.sPrev.y - 2, 30, mOpen.sPrev.y + 2, fgOpen, bgOpen);
  if (fragRatio < 0.05) pass("opening: no left step-21 fragment");
  else fail("opening: no left step-21 fragment", `fg ratio=${fragRatio.toFixed(3)} sPrev=${JSON.stringify(mOpen.sPrev)}`);

  const tEntry = T.START_BEAT * T.BEAT + T.BEAT * 0.2;
  const mEntry = await meta(page, tEntry);
  if (mEntry.ball.x < mEntry.ball.x + 1 && mEntry.ball.x < 200) pass("opening: ball enters from left");
  else fail("opening: ball enters from left", `ball.x=${mEntry.ball.x}`);

  // --- 2. Loop return: bar 21 visible + bar 22 platform ---
  const tLoop22 = (T.START_BEAT + T.PIECE_BEATS + 1) * T.BEAT;
  await page.evaluate(() => {
    window.__TEST__.boot();
  });
  const tSimEnd = tLoop22 + T.BEAT;
  await page.evaluate(
    (t0, t1) => {
      window.__TEST__.runTrack(t0, t1, 0.01);
    },
    T.START_BEAT * T.BEAT,
    tSimEnd
  );
  const mLoop = await meta(page, tLoop22);
  const sampleLoop = await drawAndSample(page, tLoop22);
  const fgLoop = mLoop.plan % 2 === 1 ? "#0d0d0d" : "#cccccc";
  const bgLoop = mLoop.plan % 2 === 1 ? "#cccccc" : "#0d0d0d";

  if (mLoop.onBar22 && mLoop.loopCount >= 1) pass("loop return: loopCount >= 1 on bar 22");
  else fail("loop return: loopCount >= 1", JSON.stringify(mLoop));

  if (lineHasFg(sampleLoop, mLoop.sCur.y, Math.max(0, mLoop.sCur.x), mLoop.sCur.x + mLoop.sCur.w, fgLoop, bgLoop))
    pass("loop return: bar 22 platform visible");
  else fail("loop return: bar 22 platform visible", JSON.stringify(mLoop.sCur));

  const s21x = mLoop.sPrev.x;
  if (s21x < 400 && lineHasFg(sampleLoop, mLoop.sPrev.y, Math.max(0, s21x), s21x + mLoop.sPrev.w, fgLoop, bgLoop, 4))
    pass("loop return: step 21 platform visible");
  else fail("loop return: step 21 visible", `sPrev=${JSON.stringify(mLoop.sPrev)}`);

  // --- 3. 22→1 drop: no bar 22 horizontal, drop join present ---
  await page.evaluate(() => window.__TEST__.boot());
  let tFall = null;
  let mFall = null;
  for (let b = 0; b < T.PIECE_BEATS; b += 0.05) {
    const t = (T.START_BEAT + T.INTRO_TOTAL_BEATS + b) * T.BEAT;
    const m = await meta(page, t);
    if (m.plan === 0 && m.beatInStep > 0 && m.beatInStep < T.REST) {
      tFall = t;
      mFall = m;
      break;
    }
  }
  if (!tFall) {
    fail("22→1 drop: find rest-fall frame", "no suitable t");
  } else {
    const sampleFall = await drawAndSample(page, tFall);
    const fgFall = mFall.plan % 2 === 1 ? "#0d0d0d" : "#cccccc";
    const bgFall = mFall.plan % 2 === 1 ? "#cccccc" : "#0d0d0d";
    const sBar22 = mFall.sPrev;
    const sBar1 = mFall.sCur;
    const horiz22 = lineHasFg(
      sampleFall,
      sBar22.y,
      Math.max(-40, sBar22.x),
      sBar22.x + sBar22.w,
      fgFall,
      bgFall,
      6
    );
    if (horiz22) pass("22→1 drop: bar 22 horizontal platform still visible");
    else fail("22→1 drop: bar 22 horizontal missing", `y=${sBar22.y}`);

    const xJoin = sBar22.x + sBar22.w;
    const yTop = Math.min(sBar22.y, sBar1.y);
    const yBot = Math.max(sBar22.y, sBar1.y);
    const joinRatio = regionFgRatio(sampleFall, xJoin - 2, yTop, xJoin + 2, yBot, fgFall, bgFall);
    if (joinRatio > 0.08) pass("22→1 drop: vertical dropJoin visible");
    else fail("22→1 drop: vertical dropJoin", `ratio=${joinRatio.toFixed(3)} xJoin=${xJoin}`);
  }

  // --- 4. Cycle step scrolls off normally (not culled while partially on screen) ---
  await page.evaluate(() => window.__TEST__.boot());
  let tScroll = null;
  let mScroll = null;
  for (let b = T.INTRO_TOTAL_BEATS + 10; b < T.PIECE_BEATS - 4; b += 0.02) {
    const t = (T.START_BEAT + b) * T.BEAT;
    const m = await meta(page, t);
    if (m.plan >= 5 && m.plan <= 15) {
      const scrollX = await page.evaluate((tt) => window.__TEST__.scrollXAt(tt), t);
      const sLeft = await page.evaluate(
        (idx, sx, tt) => window.__TEST__.stepScreen(idx, sx, tt),
        m.stepIndex - 2,
        scrollX,
        t
      );
      if (sLeft.x < 0 && sLeft.x + sLeft.w >= -40) {
        tScroll = t;
        mScroll = { ...m, sLeft, scrollX };
        break;
      }
    }
  }
  if (!tScroll) {
    fail("cycle scroll: find partially-off step", "no frame");
  } else {
    const sampleScroll = await drawAndSample(page, tScroll);
    const fgS = mScroll.plan % 2 === 1 ? "#0d0d0d" : "#cccccc";
    const bgS = mScroll.plan % 2 === 1 ? "#cccccc" : "#0d0d0d";
    const yL = mScroll.sLeft.y;
    const horiz = lineHasFg(
      sampleScroll,
      yL,
      0,
      Math.min(480, mScroll.sLeft.x + mScroll.sLeft.w),
      fgS,
      bgS,
      4
    );
    if (horiz) pass("cycle scroll: partially off-screen step still drawn");
    else fail("cycle scroll: step prematurely hidden", JSON.stringify(mScroll.sLeft));
  }

  await browser.close();
  server.close();

  console.log("");
  if (failures.length === 0) {
    console.log(`All ${8} checks passed.`);
    process.exit(0);
  } else {
    console.log(`${failures.length} check(s) failed.`);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
