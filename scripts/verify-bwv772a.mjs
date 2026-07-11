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
      loopCount = -1;
      prevPlan = -1;
      prevStepIndex = -1;
    },
    setLoop(n) { loopCount = n; },
    getLoop() { return loopCount; },
    runTrack(t0, t1, step) {
      for (let t = t0; t <= t1; t += step) trackLoop(t);
    },
    trackAt(t) {
      trackLoop(t);
    },
    drawAt(t) {
      trackLoop(t);
      draw(t);
    },
    locate,
    scrollXAt,
    stepScreen,
    isBar22,
    isFirstOpening,
    planOf,
    stepKind,
    ballState,
    START_BEAT,
    BEAT,
    PIECE_BEATS,
    N_STEPS,
    INTRO_TOTAL_BEATS,
    FIRST_PLAY_BAR_SHOW_AFTER,
    REST,
    W,
    H,
    DARK,
    LIGHT,
    ORIGIN_Y,
    STEP_H,
    cumDropUpTo,
    cumWidthUpTo,
    stepWidth,
    BX,
    BALL_R,
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
  await page.evaluate(() => new Promise((r) => requestAnimationFrame(r)));

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

  // --- 0. Before start: idle bar 22 preview (same full step as loop return)
  const preStart = await samplePage(page);
  const preMeta = await page.evaluate(() => {
    const T = window.__TEST__;
    const plan = T.N_STEPS - 1;
    const scrollX = T.cumWidthUpTo(plan);
    return T.stepScreen(plan, scrollX, T.START_BEAT * T.BEAT);
  });
  const preLine = lineHasFg(
    preStart,
    preMeta.y,
    Math.max(0, preMeta.x),
    preMeta.x + preMeta.w,
    "#cccccc",
    "#0d0d0d",
    4
  );
  if (preLine) pass("pre-start: bar 22 idle platform visible");
  else fail("pre-start: bar 22 idle platform visible", "no fg on platform");

  const preLeft = fgAt(preStart, Math.max(5, preMeta.x), preMeta.y, "#cccccc", "#0d0d0d");
  if (preLeft) pass("pre-start: bar 22 left edge visible");
  else fail("pre-start: bar 22 left edge visible", JSON.stringify(preMeta));

  const preBall = regionFgRatio(
    preStart,
    preMeta.x,
    preMeta.y - 80,
    preMeta.x + preMeta.w,
    preMeta.y - 20,
    "#cccccc",
    "#0d0d0d"
  );
  if (preBall < 0.05) pass("pre-start: no ball");
  else fail("pre-start: no ball", `ratio=${preBall.toFixed(3)}`);

  await page.evaluate(() => window.__TEST__.boot());
  const tOpen = (T.START_BEAT + T.INTRO_TOTAL_BEATS * 0.5) * T.BEAT;
  const mOpen = await meta(page, tOpen);
  await page.evaluate(() => {
    window.__TEST__.loopCount = -1;
    window.__TEST__.prevPlan = -1;
    window.__TEST__.prevStepIndex = -1;
  });
  const sampleOpen = await drawAndSample(page, tOpen);
  const fgOpen = mOpen.plan % 2 === 1 ? "#0d0d0d" : "#cccccc";
  const bgOpen = mOpen.plan % 2 === 1 ? "#cccccc" : "#0d0d0d";
  const y22 = mOpen.sCur.y;

  if (mOpen.onBar22 && mOpen.loopCount < 0) pass("opening: on bar 22, loopCount -1");
  else fail("opening: on bar 22, loopCount -1", JSON.stringify(mOpen));

  if (
    lineHasFg(
      sampleOpen,
      y22,
      Math.max(0, mOpen.sCur.x),
      mOpen.sCur.x + mOpen.sCur.w,
      fgOpen,
      bgOpen
    )
  )
    pass("opening: bar 22 horizontal platform visible");
  else fail("opening: bar 22 horizontal platform visible", `y=${y22} sCur=${JSON.stringify(mOpen.sCur)}`);

  const fragRatio = regionFgRatio(sampleOpen, 0, mOpen.sPrev.y - 2, 30, mOpen.sPrev.y + 2, fgOpen, bgOpen);
  if (fragRatio < 0.08) pass("opening: no left step-21 fragment");
  else fail("opening: no left step-21 fragment", `fg ratio=${fragRatio.toFixed(3)} sPrev=${JSON.stringify(mOpen.sPrev)}`);

  let stubFail = null;
  for (const frac of [0.2, 0.5, 0.8]) {
    const t = (T.START_BEAT + T.INTRO_TOTAL_BEATS * frac) * T.BEAT;
    const m = await meta(page, t);
    const sample = await drawAndSample(page, t);
    const fg = m.plan % 2 === 1 ? "#0d0d0d" : "#cccccc";
    const bg = m.plan % 2 === 1 ? "#cccccc" : "#0d0d0d";
    if (m.sCur.x > 8) {
      const xEnd = m.ball && m.ball.x < m.sCur.x - 10
        ? m.ball.x - 10
        : m.sCur.x - 4;
      if (xEnd > 12) {
        const stub = regionFgRatio(sample, 0, m.sCur.y - 1, xEnd, m.sCur.y + 1, fg, bg);
        if (stub > 0.05) stubFail = `frac=${frac} stub=${stub.toFixed(3)} sCur.x=${m.sCur.x.toFixed(1)}`;
      }
    }
  }
  if (!stubFail) pass("opening: no horizontal stub left of bar 22 during scroll");
  else fail("opening: no horizontal stub left of bar 22", stubFail);

  const tEntry = T.START_BEAT * T.BEAT + T.BEAT * 0.2;
  const mEntry = await meta(page, tEntry);
  if (mEntry.ball.x < mEntry.ball.x + 1 && mEntry.ball.x < 200) pass("opening: ball enters from left");
  else fail("opening: ball enters from left", `ball.x=${mEntry.ball.x}`);

  // --- 0b. First play on bar 22 before 2 bars: still no step 21 ---
  await page.evaluate(() => {
    window.__TEST__.boot();
    window.__TEST__.loopCount = -1;
  });
  const tBar22Early = (T.START_BEAT + 3) * T.BEAT;
  const mEarly = await meta(page, tBar22Early);
  const sampleEarly = await drawAndSample(page, tBar22Early);
  const fgEarly = mEarly.plan % 2 === 1 ? "#0d0d0d" : "#cccccc";
  const bgEarly = mEarly.plan % 2 === 1 ? "#cccccc" : "#0d0d0d";
  const s21Early = await page.evaluate((t) => {
    const T = window.__TEST__;
    const loc = T.locate(t);
    const sx = T.scrollXAt(t);
    const i21 = loc.stepIndex - 1;
    return T.stepScreen(i21, sx, t);
  }, tBar22Early);
  const early21 = regionFgRatio(
    sampleEarly,
    Math.max(0, s21Early.x),
    s21Early.y - 2,
    s21Early.x + s21Early.w,
    s21Early.y + 2,
    fgEarly,
    bgEarly
  );
  if (mEarly.onBar22 && mEarly.loopCount < 0 && tBar22Early < (await page.evaluate(() => window.__TEST__.FIRST_PLAY_BAR_SHOW_AFTER))) {
    if (early21 < 0.08) pass("first play before 2 bars: no step 21 on bar 22");
    else fail("first play before 2 bars: no step 21 on bar 22", `ratio=${early21.toFixed(3)} s21=${JSON.stringify(s21Early)}`);
  } else {
    fail("first play before 2 bars: no step 21 on bar 22", `not on bar22 ${JSON.stringify(mEarly)}`);
  }

  // --- 1b. First playthrough on step 21: full platform while loopCount still -1 ---
  await page.evaluate(() => window.__TEST__.boot());
  let tFirst21 = null;
  let mFirst21 = null;
  for (let b = T.INTRO_TOTAL_BEATS + 4; b < T.PIECE_BEATS - 2; b += 0.05) {
    const t = (T.START_BEAT + b) * T.BEAT;
    await page.evaluate(
      (tt) => {
        window.__TEST__.trackAt(tt);
      },
      t
    );
    const m = await meta(page, t);
    if (m.plan === T.N_STEPS - 2 && m.loopCount < 0) {
      tFirst21 = t;
      mFirst21 = m;
      break;
    }
  }
  if (!tFirst21) {
    fail("first play: step 21 frame while loopCount -1", "no frame");
  } else {
    const sampleFirst21 = await drawAndSample(page, tFirst21);
    const fg21 = mFirst21.plan % 2 === 1 ? "#0d0d0d" : "#cccccc";
    const bg21 = mFirst21.plan % 2 === 1 ? "#cccccc" : "#0d0d0d";
    if (
      lineHasFg(
        sampleFirst21,
        mFirst21.sCur.y,
        Math.max(0, mFirst21.sCur.x),
        mFirst21.sCur.x + mFirst21.sCur.w,
        fg21,
        bg21,
        4
      )
    ) {
      pass("first play: step 21 full width while loopCount -1");
    } else {
      fail("first play: step 21 full width while loopCount -1", JSON.stringify(mFirst21.sCur));
    }
  }

  // --- 1c. First 21→22 REST: step 21 platform visible (not hidden like intro) ---
  await page.evaluate(() => window.__TEST__.boot());
  let tFirst2122 = null;
  let m2122 = null;
  for (let b = T.INTRO_TOTAL_BEATS; b < T.PIECE_BEATS + T.REST; b += 0.01) {
    const t = (T.START_BEAT + b) * T.BEAT;
    await page.evaluate((tt) => window.__TEST__.trackAt(tt), t);
    const m = await meta(page, t);
    if (
      m.onBar22 &&
      m.plan === T.N_STEPS - 1 &&
      m.sPrev.w === 100 &&
      m.beatInStep > 0.05 &&
      m.beatInStep < T.REST
    ) {
      tFirst2122 = t;
      m2122 = m;
      break;
    }
  }
  if (!tFirst2122) {
    fail("first 21→22: find REST frame", "no frame");
  } else {
    const sample2122 = await drawAndSample(page, tFirst2122);
    const fg2122 = m2122.plan % 2 === 1 ? "#0d0d0d" : "#cccccc";
    const bg2122 = m2122.plan % 2 === 1 ? "#cccccc" : "#0d0d0d";
    if (
      lineHasFg(
        sample2122,
        m2122.sPrev.y,
        Math.max(0, m2122.sPrev.x),
        m2122.sPrev.x + m2122.sPrev.w,
        fg2122,
        bg2122,
        4
      )
    ) {
      pass("first 21→22: step 21 platform visible during REST");
    } else {
      fail("first 21→22: step 21 during REST", `sPrev=${JSON.stringify(m2122.sPrev)}`);
    }
  }

  // --- 1d. After intro on bar 1: no ghost step 21 on the left ---
  await page.evaluate(() => window.__TEST__.boot());
  let tBar1 = null;
  for (let b = T.INTRO_TOTAL_BEATS + 0.5; b < T.PIECE_BEATS; b += 0.05) {
    const t = (T.START_BEAT + b) * T.BEAT;
    await page.evaluate((tt) => window.__TEST__.trackAt(tt), t);
    const m = await meta(page, t);
    if (m.plan === 0 && m.loopCount < 0) {
      tBar1 = t;
      break;
    }
  }
  if (!tBar1) {
    fail("after intro: find bar 1 frame", "no frame");
  } else {
    const sampleBar1 = await drawAndSample(page, tBar1);
    const mBar1 = await meta(page, tBar1);
    const fg1 = mBar1.plan % 2 === 1 ? "#0d0d0d" : "#cccccc";
    const bg1 = mBar1.plan % 2 === 1 ? "#cccccc" : "#0d0d0d";
    const s21 = await page.evaluate((t) => {
      const T = window.__TEST__;
      const loc = T.locate(t);
      const sx = T.scrollXAt(t);
      const i21 = loc.stepIndex - loc.plan + (T.N_STEPS - 2);
      return T.stepScreen(i21, sx, t);
    }, tBar1);
    const ghost21 = regionFgRatio(
      sampleBar1,
      Math.max(0, s21.x),
      s21.y - 2,
      s21.x + s21.w,
      s21.y + 2,
      fg1,
      bg1
    );
    if (ghost21 < 0.05) pass("after intro: no ghost step 21 on bar 1");
    else fail("after intro: ghost step 21 on bar 1", `ratio=${ghost21.toFixed(3)} s21=${JSON.stringify(s21)}`);
  }

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

  if (mLoop.onBar22 && mLoop.loopCount >= 0) pass("loop return: loopCount >= 0 on bar 22");
  else fail("loop return: loopCount >= 0", JSON.stringify(mLoop));

  if (lineHasFg(sampleLoop, mLoop.sCur.y, Math.max(0, mLoop.sCur.x), mLoop.sCur.x + mLoop.sCur.w, fgLoop, bgLoop))
    pass("loop return: bar 22 platform visible");
  else fail("loop return: bar 22 platform visible", JSON.stringify(mLoop.sCur));

  const s21x = mLoop.sPrev.x;
  if (s21x < 400 && lineHasFg(sampleLoop, mLoop.sPrev.y, Math.max(0, s21x), s21x + mLoop.sPrev.w, fgLoop, bgLoop, 4))
    pass("loop return: step 21 platform visible");
  else fail("loop return: step 21 visible", `sPrev=${JSON.stringify(mLoop.sPrev)}`);

  // --- 2b. 21→22: smooth lift (not instant jump) ---
  await page.evaluate(() => window.__TEST__.boot());
  const tLoopStart = (T.START_BEAT + T.PIECE_BEATS - 0.5) * T.BEAT;
  const tLoopEnd = (T.START_BEAT + T.PIECE_BEATS + T.REST) * T.BEAT;
  await page.evaluate(
    (t0, t1) => {
      window.__TEST__.runTrack(t0, t1, 0.005);
    },
    T.START_BEAT * T.BEAT,
    tLoopEnd
  );
  const liftYs = [];
  for (let b = 0; b <= T.REST; b += 0.02) {
    const t = (T.START_BEAT + T.PIECE_BEATS + b) * T.BEAT;
    const y = await page.evaluate((t) => {
      const x = window.__TEST__;
      const l = x.locate(t);
      const sx = x.scrollXAt(t);
      return x.stepScreen(l.stepIndex, sx, t).y;
    }, t);
    liftYs.push(y);
  }
  let maxStep = 0;
  for (let i = 1; i < liftYs.length; i++) {
    maxStep = Math.max(maxStep, Math.abs(liftYs[i] - liftYs[i - 1]));
  }
  const totalLift = liftYs.length ? liftYs[liftYs.length - 1] - liftYs[0] : 0;
  if (totalLift < -20 && maxStep < 25) pass("21→22: smooth camera lift during REST");
  else fail("21→22: smooth camera lift", `totalLift=${totalLift.toFixed(1)} maxStep=${maxStep.toFixed(1)}`);

  const ballYs = [];
  const stepYs = [];
  for (let b = 0; b <= T.REST; b += 0.02) {
    const t = (T.START_BEAT + T.PIECE_BEATS + b) * T.BEAT;
    const sample = await page.evaluate((t) => {
      const x = window.__TEST__;
      const l = x.locate(t);
      const sx = x.scrollXAt(t);
      return {
        ballY: x.ballState(t).y,
        stepY: x.stepScreen(l.stepIndex, sx, t).y,
      };
    }, t);
    ballYs.push(sample.ballY);
    stepYs.push(sample.stepY);
  }
  let maxBallStep = 0;
  for (let i = 1; i < ballYs.length; i++) {
    maxBallStep = Math.max(maxBallStep, Math.abs(ballYs[i] - ballYs[i - 1]));
  }
  const ballRange = ballYs.length
    ? Math.max(...ballYs) - Math.min(...ballYs)
    : 0;
  const stepLift = stepYs.length ? stepYs[0] - stepYs[stepYs.length - 1] : 0;
  if (stepLift > 20 && ballRange < 8 && maxBallStep < 8) {
    pass("21→22: ball fixed like cycle REST (not platform tracking)");
  } else {
    fail(
      "21→22: ball REST motion",
      `stepLift=${stepLift.toFixed(1)} ballRange=${ballRange.toFixed(1)} maxBallStep=${maxBallStep.toFixed(1)}`
    );
  }

  // --- 3. 22→1 drop: bar 22 horizontal + drop join ---
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
    console.log(`All ${19} checks passed.`);
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
