#!/usr/bin/env node
// Seslendirme kaydını videonun zaman çizelgesine yerleştirir.
//
//   node seslendirme.js kayit.mp3      → tek dosya: satırlar sırayla, aralarında ~1 sn sessizlik
//   node seslendirme.js satirlar/      → satır başına ayrı dosya: 01.wav, 02.wav … (mp3/wav/m4a)
//   node seslendirme.js cikti/raf/     → VoxCPM2 ses tasarımı aracının çıktısı (okuma.wav + ozet.json)
//
// Çıktı: seslendirme/seslendirme.wav (render.js kullanır) ve seslendirme/seslendirme.mp3 (önizleme sayfası).
// Satır başlangıçları ve süre sınırları seslendirme/zamanlama.json dosyasındadır.
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const SR = 48000;
const HERE = __dirname;
const plan = JSON.parse(fs.readFileSync(path.join(HERE, 'seslendirme', 'zamanlama.json'), 'utf8'));
const lines = plan.satirlar;
const src = process.argv[2];
if (!src) { console.error('Kullanım: node seslendirme.js kayit.mp3  |  node seslendirme.js satirlar/'); process.exit(1); }

function decode(file, filters) {
  const args = ['-v', 'error', '-i', file, '-ac', '1', '-ar', String(SR)];
  if (filters) args.push('-af', filters);
  args.push('-f', 'f32le', '-');
  const r = spawnSync('ffmpeg', args, { maxBuffer: 1 << 30 });
  if (r.status !== 0) throw new Error(`${file} okunamadı: ${r.stderr}`);
  return new Float32Array(r.stdout.buffer, r.stdout.byteOffset, r.stdout.length / 4);
}
function encode(samples, file, extra = []) {
  const r = spawnSync('ffmpeg', ['-y', '-v', 'error', '-f', 'f32le', '-ar', String(SR), '-ac', '1', '-i', '-', ...extra, file],
    { input: Buffer.from(samples.buffer, samples.byteOffset, samples.byteLength) });
  if (r.status !== 0) throw new Error(`${file} yazılamadı: ${r.stderr}`);
}
function stretch(samples, rate) {
  // ses perdesini koruyarak hızlandır (ffmpeg atempo)
  const tmp = path.join(HERE, 'seslendirme', '.tmp.wav');
  encode(samples, tmp);
  const out = decode(tmp, `atempo=${rate.toFixed(4)}`);
  fs.unlinkSync(tmp);
  return out;
}

// 10 ms çerçevelerde enerji ve konuşma/sessizlik maskesi
const HOP = SR / 100;
function activity(x) {
  const n = Math.floor(x.length / HOP), db = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    let s = 0; for (let k = 0; k < HOP; k++) { const v = x[i * HOP + k]; s += v * v; }
    db[i] = 10 * Math.log10(s / HOP + 1e-12);
  }
  const sorted = Array.from(db).sort((a, b) => a - b);
  const thr = Math.max(sorted[Math.floor(n * .95)] - 38, -60);
  return { db, on: Array.from(db, v => v > thr) };
}
function speechRuns(on) {
  const runs = []; let s = -1;
  on.forEach((v, i) => { if (v && s < 0) s = i; if (!v && s >= 0) { runs.push([s, i]); s = -1; } });
  if (s >= 0) runs.push([s, on.length]);
  // 60 ms'den kısa kopuklukları birleştir, 40 ms'den kısa patlamaları at
  const merged = [];
  for (const r of runs) {
    if (merged.length && r[0] - merged[merged.length - 1][1] < 6) merged[merged.length - 1][1] = r[1];
    else merged.push(r.slice());
  }
  return merged.filter(r => r[1] - r[0] >= 4);
}
function trim(x) {
  const runs = speechRuns(activity(x).on);
  if (!runs.length) return x.subarray(0, 0);
  const a = Math.max(0, runs[0][0] * HOP - SR * .03), b = Math.min(x.length, runs[runs.length - 1][1] * HOP + SR * .09);
  return x.slice(a, b);
}
function fade(x) {
  const fi = Math.min(x.length, SR * .006), fo = Math.min(x.length, SR * .05);
  for (let i = 0; i < fi; i++) x[i] *= i / fi;
  for (let i = 0; i < fo; i++) x[x.length - 1 - i] *= i / fo;
  return x;
}

// --- satırları çıkar ---
let segs = [];
const ozet = path.join(src, 'ozet.json');
if (fs.statSync(src).isDirectory() && fs.existsSync(ozet)) {
  // VoxCPM2 ses tasarımı aracının çıktı klasörü: okuma.wav + ozet.json (satır başına t0/t1)
  const sum = JSON.parse(fs.readFileSync(ozet, 'utf8'));
  if (sum.satirlar.length !== lines.length) throw new Error(`${lines.length} satır bekleniyordu, ozet.json içinde ${sum.satirlar.length} satır var.`);
  const x = decode(path.join(src, 'okuma.wav'));
  segs = sum.satirlar.map(r => trim(x.slice(Math.round(r.t0 * SR), Math.round(r.t1 * SR))));
  console.log(`VoxCPM2 okuması: ${sum.ses} · ${sum.ses_sn} sn${sum.supheli_satirlar && sum.supheli_satirlar.length ? ' · kontrol edilecek satırlar: ' + sum.supheli_satirlar.join(', ') : ''}`);
} else if (fs.statSync(src).isDirectory()) {
  const files = fs.readdirSync(src).filter(f => /\.(wav|mp3|m4a|aac|flac|ogg)$/i.test(f)).sort();
  if (files.length !== lines.length) throw new Error(`${lines.length} satır bekleniyordu, klasörde ${files.length} ses dosyası var.`);
  segs = files.map(f => trim(decode(path.join(src, f))));
} else {
  const x = decode(src);
  const runs = speechRuns(activity(x).on);
  // satırlar arasındaki en uzun N-1 sessizliği sınır kabul et
  const gaps = runs.slice(1).map((r, i) => ({ i, len: r[0] - runs[i][1] }));
  const cuts = gaps.slice().sort((a, b) => b.len - a.len).slice(0, lines.length - 1).map(g => g.i).sort((a, b) => a - b);
  if (runs.length < lines.length) throw new Error(`Kayıtta ${lines.length} satır bulunamadı (${runs.length} konuşma bölümü). Satır aralarına ~1 sn sessizlik bırakın.`);
  const shortest = Math.min(...cuts.map(i => gaps[i].len)) / 100;
  const longestInside = Math.max(0, ...gaps.filter(g => !cuts.includes(g.i)).map(g => g.len)) / 100;
  if (shortest < longestInside + .15) console.warn(`Uyarı: satır arası en kısa sessizlik ${shortest.toFixed(2)} sn, satır içi en uzun duraklama ${longestInside.toFixed(2)} sn. Bölme yanlış olabilir; tabloyu kontrol edin.`);
  let start = 0;
  for (const c of [...cuts, runs.length - 1]) {
    const a = runs[start][0] * HOP, b = runs[c][1] * HOP;
    segs.push(trim(x.slice(Math.max(0, a - SR * .05), Math.min(x.length, b + SR * .12))));
    start = c + 1;
  }
}

// --- yerleştir ---
const N = Math.round(plan.sure * SR);
const out = new Float32Array(N);
console.log('No  Başlangıç  Süre   Sınır  Durum');
lines.forEach((ln, i) => {
  let s = segs[i];
  const room = ln.son - ln.bas;
  let dur = s.length / SR, note = 'sığıyor';
  if (dur > room) {
    const rate = dur / room;
    if (rate <= 1.15) { s = stretch(s, rate); note = `%${Math.round((rate - 1) * 100)} hızlandırıldı`; }
    else note = `SIĞMIYOR (${(dur - room).toFixed(2)} sn taşıyor)`;
  }
  fade(s);
  const at = Math.round(ln.bas * SR);
  for (let k = 0; k < s.length && at + k < N; k++) out[at + k] += s[k];
  // satır içi duraklamalar: anahtar kelime / seçenek zamanlamasını ayarlamak için
  const runs = speechRuns(activity(s).on);
  const inner = runs.slice(1).filter((r, j) => r[0] - runs[j][1] >= 18).map(r => (ln.bas + r[0] / 100).toFixed(2));
  console.log(`${String(ln.no).padStart(2)}  ${ln.bas.toFixed(2).padStart(6)}   ${(s.length / SR).toFixed(2)}  ${room.toFixed(2)}  ${note}${inner.length ? '   duraklama sonrası: ' + inner.join(', ') : ''}`);
});

let peak = 0; for (const v of out) peak = Math.max(peak, Math.abs(v));
const g = peak > 0 ? Math.pow(10, -1.5 / 20) / peak : 1;
for (let i = 0; i < N; i++) out[i] *= g;

const dir = path.join(HERE, 'seslendirme');
encode(out, path.join(dir, 'seslendirme.wav'), ['-c:a', 'pcm_s16le']);
encode(out, path.join(dir, 'seslendirme.mp3'), ['-c:a', 'libmp3lame', '-b:a', '128k']);
console.log(`\nYazıldı: seslendirme/seslendirme.wav ve seslendirme/seslendirme.mp3 (${plan.sure} sn)`);
console.log('Videoyu yeniden üretmek için: node render.js');
