// Kütle modelinin render görüntülerini üretir: node render.mjs [genişlik yükseklik ölçek]
// Çıktılar renders/ klasörüne yazılır. three.js yerel node_modules'tan sunulur.
import { createRequire } from 'node:module';
import { readFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const KOK = path.dirname(fileURLToPath(import.meta.url));
const THREE_DIZIN = path.join(KOK, 'node_modules', 'three');

const [W = 1600, H = 1000, OLCEK = 2] = process.argv.slice(2).map(Number);
const GORUNUSLER = [
  ['01_kuzeydogu_kusbakisi', 'mod=render&gorunus=kuzeydogu'],
  ['02_706_sokak_cephesi', 'mod=render&gorunus=sokak'],
  ['03_706_sokak_yaya_bakisi', 'mod=render&gorunus=kose'],
  ['04_guneybati_kusbakisi', 'mod=render&gorunus=guneybati'],
  ['05_vaziyet_ustten', 'mod=render&gorunus=vaziyet'],
  ['06_kullanim_semasi', 'mod=diyagram&gorunus=diyagram'],
];
const tip = f => f.endsWith('.js') ? 'application/javascript' : f.endsWith('.html') ? 'text/html' : 'application/octet-stream';

const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: OLCEK });
page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log('[tarayıcı]', m.text()); });
page.on('pageerror', e => console.log('[sayfa hatası]', e.message));
await page.route('https://cdn.jsdelivr.net/npm/three@0.160.0/**', async r => {
  const yol = new URL(r.request().url()).pathname.replace('/npm/three@0.160.0/', '');
  await r.fulfill({ body: await readFile(path.join(THREE_DIZIN, yol)), contentType: tip(yol) });
});
await page.route('http://kutle.yerel/**', async r => {
  const yol = new URL(r.request().url()).pathname.slice(1) || 'index.html';
  await r.fulfill({ body: await readFile(path.join(KOK, yol)), contentType: tip(yol) });
});

await mkdir(path.join(KOK, 'renders'), { recursive: true });
const sadece = process.env.GORUNUS;
if (process.env.SORGU) GORUNUSLER.push(['test_' + (process.env.AD || 'ozel'), process.env.SORGU]);
for (const [ad, sorgu] of GORUNUSLER) {
  if (sadece && !ad.includes(sadece)) continue;
  if (process.env.SORGU && !ad.startsWith('test_')) continue;
  const t0 = Date.now();
  await page.goto(`http://kutle.yerel/index.html?${sorgu}&ui=0`);
  await page.waitForFunction(() => window.__hazir === true, null, { timeout: 300000 });
  const dosya = path.join(KOK, 'renders', ad + '.png');
  await page.screenshot({ path: dosya, timeout: 300000 });
  console.log(`${ad}.png  ${((Date.now() - t0) / 1000).toFixed(1)} sn`);
}
await browser.close();
