#!/usr/bin/env node
// Raf Analiz reel → 1080×1920 MP4 (ve kapak / tek kare PNG).
// Kullanım:
//   node render.js                      → cikti/raf-analiz-100tl.mp4 + kapak
//   node render.js --fps 24 --out x.mp4
//   node render.js --frames 2.6,8.5,14  → seçilen saniyelerin PNG kareleri
//   node render.js --preview            → yarı çözünürlük, 15 fps hızlı deneme
//   node render.js --sessiz             → efekt sesi olmadan (sessiz ses kanalı)
//   node render.js --ses-wav            → efekt sesini ayrıca .wav olarak da kaydet
//   node render.js --yalnizca-ses       → video üretmeden yalnızca son ses karışımını (.m4a) çıkar
//   node render.js --seslendirmesiz     → seslendirme dosyası olsa bile yalnızca efektler
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

const args = process.argv.slice(2);
const opt = (name, def) => { const i = args.indexOf('--' + name); return i >= 0 ? args[i + 1] : def; };
const has = name => args.includes('--' + name);

const HERE = __dirname;
const OUT_DIR = path.join(HERE, 'cikti');
const preview = has('preview');
const fps = Number(opt('fps', preview ? 15 : 30));
const scale = preview ? 0.5 : 1;
const out = path.resolve(opt('out', path.join(OUT_DIR, preview ? 'raf-analiz-100tl.onizleme.mp4' : 'raf-analiz-100tl.mp4')));
const frames = opt('frames', null);
const coverAt = Number(opt('cover', '3.0'));

function wrapped() {
  // Yayın sırasında sayfa bir <!doctype html> iskeletine sarılır; burada da aynısını yapıyoruz.
  const body = fs.readFileSync(path.join(HERE, 'reel.html'), 'utf8');
  return `<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><style>:root{color-scheme:light}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style></head><body>${body}</body></html>`;
}

(async () => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const tmp = path.join(OUT_DIR, '.render.html');
  fs.writeFileSync(tmp, wrapped());

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: scale });
  await page.addInitScript(() => { window.__REEL_EXPORT__ = true; });
  page.on('pageerror', e => console.error('Sayfa hatası:', e.message));
  await page.goto('file://' + tmp, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => window.__reel && window.__reel.ready, null, { timeout: 30000 });
  const fontsOk = await page.evaluate(() => document.fonts.check('900 100px Archivo') && document.fonts.check('600 20px "IBM Plex Mono"'));
  if (!fontsOk) console.warn('Uyarı: Google Fonts yüklenemedi, yedek yazı tipi kullanılıyor.');
  const duration = await page.evaluate(() => window.__reel.duration);
  const clip = { x: 0, y: 0, width: 1080, height: 1920 };

  const shot = async (t, file) => {
    await page.evaluate(tt => window.__reel.seek(tt), t);
    return page.screenshot({ clip, type: 'png', path: file });
  };

  if (frames) {
    for (const s of frames.split(',').map(Number)) {
      const file = path.join(OUT_DIR, `kare-${s.toFixed(2)}.png`);
      await shot(s, file);
      console.log(file);
    }
    await browser.close();
    fs.unlinkSync(tmp);
    return;
  }

  // Ses: sayfadaki sentezleyici, animasyonla aynı zaman çizelgesinden efekt kanalını üretir.
  // seslendirme/seslendirme.wav varsa (node seslendirme.js ile üretilir) efektler konuşmanın altında kısılarak karıştırılır.
  let audioIn = ['-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000'];
  let graph = base => ({ filter: null, map: `${base}:a` });
  const vo = path.join(HERE, 'seslendirme', 'seslendirme.wav');
  const useVo = !has('sessiz') && !has('seslendirmesiz') && fs.existsSync(vo);
  if (!has('sessiz')) {
    const b64 = await page.evaluate(() => window.__reel.audio(48000));
    const pcm = path.join(OUT_DIR, '.ses.pcm');
    fs.writeFileSync(pcm, Buffer.from(b64, 'base64'));
    audioIn = ['-f', 's16le', '-ar', '48000', '-ac', '2', '-i', pcm];
    if (useVo) {
      audioIn.push('-i', vo);
      graph = base => ({
        filter: `[${base + 1}:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[v1][v2];` +
          `[${base}:a][v1]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=350[s];[s]volume=0.75[s2];` +
          `[s2][v2]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000[a]`,
        map: '[a]',
      });
    }
    const audioOnly = (file, codec) => new Promise((res, rej) => {
      const g = graph(0);
      spawn('ffmpeg', ['-y', '-loglevel', 'error', ...audioIn, ...(g.filter ? ['-filter_complex', g.filter] : []), '-map', g.map, ...codec, file], { stdio: 'inherit' })
        .on('close', c => (c === 0 ? res() : rej(new Error('ses dışa aktarılamadı'))));
    });
    if (has('ses-wav')) await audioOnly(out.replace(/\.mp4$/, '.ses.wav'), []);
    if (has('yalnizca-ses')) {
      const file = out.replace(/\.mp4$/, '.ses.m4a');
      await audioOnly(file, ['-c:a', 'aac', '-b:a', '160k']);
      console.log(`Ses: ${file}${useVo ? ' (seslendirme + efektler)' : ' (yalnızca efektler)'}`);
      await browser.close(); fs.unlinkSync(tmp); fs.unlinkSync(pcm);
      return;
    }
  }
  if (useVo) console.log('Seslendirme ekleniyor: seslendirme/seslendirme.wav');

  const N = Math.round(duration * fps);
  const g = graph(1);
  const ff = spawn('ffmpeg', [
    '-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    ...audioIn,
    ...(g.filter ? ['-filter_complex', g.filter] : []),
    '-map', '0:v', '-map', g.map, '-t', String(N / fps),
    '-c:v', 'libx264', '-preset', preview ? 'veryfast' : 'slow', '-crf', preview ? '24' : '17',
    '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.1',
    '-c:a', 'aac', '-b:a', '128k',
    '-movflags', '+faststart', out,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg çıkış kodu ' + c)))));

  const t0 = Date.now();
  for (let i = 0; i < N; i++) {
    await page.evaluate(tt => window.__reel.seek(tt), i / fps);
    const buf = await page.screenshot({ clip, type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % fps === 0) process.stdout.write(`\r${(i / fps).toFixed(0).padStart(2)} / ${duration.toFixed(0)} sn`);
  }
  ff.stdin.end();
  await done;
  process.stdout.write(`\rVideo: ${out}  (${((Date.now() - t0) / 1000).toFixed(0)} sn)\n`);

  const cover = out.replace(/\.mp4$/, '.kapak.png');
  await shot(coverAt, cover);
  console.log('Kapak: ' + cover);
  await browser.close();
  fs.unlinkSync(tmp);
  const pcm = path.join(OUT_DIR, '.ses.pcm');
  if (fs.existsSync(pcm)) fs.unlinkSync(pcm);
})().catch(e => { console.error(e); process.exit(1); });
