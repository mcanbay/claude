// Kütle + cephe tasarımını (mod=tasarim) GLB olarak dışa aktarır: node blender/disa_aktar.mjs
import { createRequire } from 'node:module';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const KOK = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const tip = f => f.endsWith('.js') ? 'application/javascript' : 'text/html';
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 400, height: 300 } });
p.on('pageerror', e => console.log('[sayfa hatası]', e.message));
await p.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
await p.route('https://cdn.jsdelivr.net/npm/three@0.160.0/**', async r => {
  const yol = new URL(r.request().url()).pathname.replace('/npm/three@0.160.0/', '');
  await r.fulfill({ body: await readFile(path.join(KOK, 'node_modules', 'three', yol)), contentType: tip(yol) });
});
await p.route('http://kutle.yerel/**', async r => {
  const yol = new URL(r.request().url()).pathname.slice(1);
  await r.fulfill({ body: await readFile(path.join(KOK, yol)), contentType: tip(yol) });
});
await p.goto('http://kutle.yerel/index.html?mod=tasarim&ui=0&ao=0');
await p.waitForFunction(() => window.__hazir === true, null, { timeout: 120000 });
const b64 = await p.evaluate(() => window.__glbAl());
const cikti = process.argv[2] || path.join(KOK, 'blender', 'model_tasarim.glb');
await writeFile(cikti, Buffer.from(b64, 'base64'));
console.log('GLB:', cikti, (Buffer.from(b64, 'base64').length / 1e6).toFixed(1), 'MB');
await b.close();
