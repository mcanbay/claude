// Etkileşimli modeli tek, bağımsız bir HTML dosyasına paketler: node tek_dosya.mjs
// three.js ve kutle.js dosyanın içine gömülür; internet bağlantısı olmadan da açılır.
import { build } from 'esbuild';
import { readFile, writeFile, mkdir, unlink } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const KOK = path.dirname(fileURLToPath(import.meta.url));
let html = await readFile(path.join(KOK, 'index.html'), 'utf8');

const bas = html.indexOf('<script type="module">'), son = html.indexOf('</script>', bas);
let kod = html.slice(bas + '<script type="module">'.length, son);
// Blender dışa aktarım kancası bağımsız dosyada gerekmez
kod = kod.replace(/\/\/ Blender'a aktarım[\s\S]*?\n};\n/, '');

const giris = path.join(KOK, '.tek_dosya_giris.mjs');
await writeFile(giris, kod);
const sonuc = await build({
  entryPoints: [giris], bundle: true, format: 'iife', minify: true, write: false,
  target: 'es2020', legalComments: 'inline', logLevel: 'warning',
});
await unlink(giris);
const paket = sonuc.outputFiles[0].text.replace(/<\/script/gi, '<\\/script');

html = html.replace(/<script type="importmap">[\s\S]*?<\/script>\n?/, '');
const b2 = html.indexOf('<script type="module">'), s2 = html.indexOf('</script>', b2) + '</script>'.length;
html = html.slice(0, b2) + '<script>\n' + paket + '\n</script>' + html.slice(s2);

await mkdir(path.join(KOK, 'dagitim'), { recursive: true });
const cikti = path.join(KOK, 'dagitim', 'index.html');
await writeFile(cikti, html);
console.log(cikti, (html.length / 1e6).toFixed(2), 'MB');
