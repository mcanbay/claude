// Render index.html frame-by-frame with headless Chromium and encode with ffmpeg.
//
//   node render.js preview 3 15 40          -> out/preview_<t>.png stills
//   node render.js video [fps] [tail]       -> out/seni_sen_yapan.mp4
//
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const OUT = path.join(ROOT, 'out');
const timings = JSON.parse(fs.readFileSync(path.join(ROOT, 'assets/timings.json'), 'utf8'));
const SCALE = 1.5; // 720x1280 css -> 1080x1920

async function open() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 720, height: 1280 }, deviceScaleFactor: SCALE });
  page.on('console', m => console.log('[page]', m.text()));
  page.on('pageerror', e => console.error('[pageerror]', e));
  await page.goto('file://' + path.join(ROOT, 'index.html'));
  await page.evaluate(t => window.setup(t), timings);
  return { browser, page };
}

async function preview(times) {
  const { browser, page } = await open();
  for (const t of times) {
    await page.evaluate(t => window.render(t), +t);
    const f = path.join(OUT, `preview_${String(t).padStart(5, '0')}.png`);
    await page.screenshot({ path: f });
    console.log(f);
  }
  await browser.close();
}

async function video(fps = 30, tail = 1.6) {
  const { browser, page } = await open();
  const dur = timings.duration + tail;
  const n = Math.ceil(dur * fps);
  const silent = path.join(OUT, 'video_silent.mp4');
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(fps), silent], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => window.render(t), i / fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 93 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 150 === 0) console.log(`frame ${i}/${n}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();

  const final = path.join(OUT, 'seni_sen_yapan.mp4');
  await new Promise((res, rej) => {
    const p = spawn('ffmpeg', ['-y', '-v', 'error', '-i', silent, '-i', path.join(ROOT, 'assets/voice.mp3'),
      '-filter_complex', `[1:a]apad=pad_dur=${tail},loudnorm=I=-15:TP=-1.5:LRA=11[a]`, '-map', '0:v', '-map', '[a]',
      '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', final], { stdio: 'inherit' });
    p.on('close', c => c === 0 ? res() : rej(new Error('ffmpeg mux failed')));
  });
  console.log('done ->', final);
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const [mode, ...rest] = process.argv.slice(2);
  if (mode === 'preview') await preview(rest.length ? rest : [2, 12, 23, 40, 62, 78, 97]);
  else await video(+(rest[0] || 30), +(rest[1] || 1.6));
})().catch(e => { console.error(e); process.exit(1); });
