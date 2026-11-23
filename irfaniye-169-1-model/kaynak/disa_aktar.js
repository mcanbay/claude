// Modeli GLB ve OBJ+MTL olarak dışa aktarır (Playwright + yerel three.js ile).
// Kullanım: node disa_aktar.js <model.html'nin sunulduğu URL> <çıktı klasörü>
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
(async () => {
  const [url, out] = process.argv.slice(2);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 800, height: 600 } });
  await p.goto(url);
  await p.waitForFunction(() => window.__model, null, { timeout: 60000 });
  const res = await p.evaluate(async () => {
    const { GLTFExporter } = await import('three/addons/exporters/GLTFExporter.js');
    const { OBJExporter } = await import('three/addons/exporters/OBJExporter.js');
    const { mergeGeometries } = await import('three/addons/utils/BufferGeometryUtils.js');
    const M = window.__model, THREE = M.THREE;
    M.setCut(3);
    const root = new THREE.Group(); root.name = 'Irfaniye_169_1';
    const mats = new Map();
    const conv = (src, name) => {
      const g = new THREE.Group(); g.name = name; g.position.copy(src.position);
      src.traverse(o => {
        if (!o.isMesh || o.material.map) return;
        if (o.isInstancedMesh) {
          const list = [], m = new THREE.Matrix4();
          for (let i = 0; i < o.count; i++) {
            o.getMatrixAt(i, m);
            const geo = o.geometry.clone().applyMatrix4(m);
            for (const k of Object.keys(geo.attributes)) if (!['position', 'normal'].includes(k)) geo.deleteAttribute(k);
            list.push(geo.index ? geo.toNonIndexed() : geo);
          }
          const mat = o.material.clone(); mat.name = name + '_' + (o.name || 'inst'); mat.color.set(o.instanceColor ? 0x5f8a48 : o.material.color);
          if (name === 'Araclar' && o.instanceColor) mat.color.set(0x8f969c);
          const mesh = new THREE.Mesh(mergeGeometries(list), mat); mesh.name = mat.name; g.add(mesh);
        } else {
          const mesh = new THREE.Mesh(o.geometry, o.material); mesh.name = o.name; g.add(mesh);
        }
      });
      root.add(g);
    };
    // name materials after their role so OBJ/MTL and GLB carry readable names
    M.levelGroups.forEach((g, i) => g.traverse(o => { if (o.isMesh) o.material.name = o.name; }));
    M.siteGroup.traverse(o => { if (o.isMesh && !o.material.map) o.material.name = o.name; });
    M.treeGroup.children.forEach((o, i) => o.name = ['agac_tac', 'agac_govde', 'cali', 'aydinlatma_direk', 'aydinlatma_baslik'][i] || 'obje');
    M.carsGroup.children.forEach((o, i) => o.name = ['arac_govde', 'arac_kabin'][i]);
    ['Zemin_Kat', '1_Kat', '2_Kat', 'Cati'].forEach((n, i) => conv(M.levelGroups[i], n));
    conv(M.siteGroup, 'Peyzaj');
    conv(M.treeGroup, 'Agaclar');
    conv(M.carsGroup, 'Araclar');
    root.updateMatrixWorld(true);
    const glb = await new GLTFExporter().parseAsync(root, { binary: true });
    const obj = new OBJExporter().parse(root);
    root.traverse(o => { if (o.isMesh) mats.set(o.material.name, o.material); });
    let mtl = '# Irfaniye 169 Ada 1 Parsel - malzemeler\n';
    for (const [n, m] of mats) {
      const c = m.color;
      mtl += `\nnewmtl ${n}\nKd ${c.r.toFixed(4)} ${c.g.toFixed(4)} ${c.b.toFixed(4)}\nKa 0 0 0\nKs 0.05 0.05 0.05\nd ${m.transparent ? m.opacity.toFixed(2) : '1.00'}\nillum 2\n`;
    }
    const bytes = new Uint8Array(glb); let bin = '';
    for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    return { glb: btoa(bin), obj: 'mtllib irfaniye_169_1.mtl\n' + obj, mtl };
  });
  fs.mkdirSync(out, { recursive: true });
  fs.writeFileSync(path.join(out, 'irfaniye_169_1.glb'), Buffer.from(res.glb, 'base64'));
  fs.writeFileSync(path.join(out, 'irfaniye_169_1.obj'), res.obj);
  fs.writeFileSync(path.join(out, 'irfaniye_169_1.mtl'), res.mtl);
  for (const f of fs.readdirSync(out)) console.log(f, fs.statSync(path.join(out, f)).size);
  await b.close();
})();
