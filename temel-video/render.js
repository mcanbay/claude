// index.html'i başsız Chromium ile kare kare çizer, ffmpeg ile mp4 yapar.
//
//   node render.js preview 1 3 6 8 12      -> out/preview_<t>.png
//   node render.js video [fps]              -> out/binanin_gorunmeyen_kahramani.mp4
//                                              (ses yoksa out/taslak.mp4)
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
  page.on('pageerror', e => { console.error('[pageerror]', e); process.exitCode = 1; });
  await page.goto('file://' + path.join(ROOT, 'index.html'));
  await page.evaluate(t => window.setup(t), timings);
  return { browser, page };
}

function run(args) {
  return new Promise((res, rej) => {
    const p = spawn('ffmpeg', args, { stdio: 'inherit' });
    p.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg failed: ' + args.join(' ')))));
  });
}

async function preview(times) {
  const { browser, page } = await open();
  for (const t of times) {
    await page.evaluate(t => window.render(t), +t);
    const f = path.join(OUT, `preview_${(+t).toFixed(2).padStart(6, '0')}.png`);
    await page.screenshot({ path: f });
    console.log(f);
  }
  await browser.close();
}

async function video(fps = 30) {
  const { browser, page } = await open();
  const n = Math.ceil(timings.duration * fps);
  const silent = path.join(OUT, 'video_silent.mp4');
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', String(fps), silent],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => window.render(t), i / fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 94 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 60 === 0) console.log(`kare ${i}/${n}  ${((Date.now() - t0) / 1000).toFixed(0)} sn`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();

  const mix = path.join(OUT, 'ses_mix.wav');
  const name = timings.mode === 'ses' ? 'binanin_gorunmeyen_kahramani.mp4' : 'taslak.mp4';
  const final = path.join(OUT, name);
  await run(['-y', '-v', 'error', '-i', silent, '-i', mix,
    '-filter_complex', '[1:a]loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000[a]', '-map', '0:v', '-map', '[a]',
    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', final]);
  console.log('bitti ->', final);
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const [mode, ...rest] = process.argv.slice(2);
  if (mode === 'preview') await preview(rest.length ? rest : [0.6, 2.6, 5.2, 7.0, 8.9, 13.5]);
  else await video(+(rest[0] || 30));
})().catch(e => { console.error(e); process.exit(1); });
