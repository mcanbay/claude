// Önizleme: projeyi bir kez paketleyip verilen karelerden kontrol görüntüsü üretir.
// Kullanım: node scripts/preview-stills.mjs <çıktı_klasörü> 0 30 90 ...
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import path from "node:path";

const [outDir, ...frames] = process.argv.slice(2);
const browserExecutable = process.env.REMOTION_CHROME || null;
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts") });
const composition = await selectComposition({ serveUrl, id: "SekQuark", browserExecutable });
for (const f of frames) {
  await renderStill({ serveUrl, composition, frame: Number(f), output: `${outDir}/f${String(f).padStart(3, "0")}.jpg`, scale: 0.5, imageFormat: "jpeg", browserExecutable });
  console.log("frame", f);
}
