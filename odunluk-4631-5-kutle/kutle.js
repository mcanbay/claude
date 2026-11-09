// Odunluk · 4631 Ada 5 Parsel — kütle modeli
//
// Bütün yatay ölçüler verilen AutoCAD çıktılarındaki (PDF) vektör
// koordinatlarından, bütün yükseklikler şematik görünüşten alınmıştır.
// Çizimde olmayan hiçbir eleman (ağaç, komşu bina, peyzaj, renk şeması)
// eklenmemiştir. Ayrıntılar README.md dosyasındadır.

import * as THREE from 'three';

// ---------------------------------------------------------------------------
// 1. Ölçek ve koordinat dönüşümleri
// ---------------------------------------------------------------------------
// Zemin kat planı (vaziyet) PDF birimi -> metre.
// Dükkan iç alanı 94,50 m² ve merdiven basamağı 28 cm aynı ölçeği verir.
export const S = 0.0196;
// Model orijini: parsel sınır kutusunun ortası (zemin kat planı birimi)
const OX = 1564.4, OY = 1260.45;

// Normal kat planı -> zemin kat planı (parsel köşeleri üzerinden en küçük
// kareler uydurması; en büyük hata 0,14 birim ≈ 3 mm)
const NK = 0.984837, NTX = -17.324, NTY = -45.550;

// Plan noktası -> dünya (X doğu, Z güney, Y yukarı)
const Z = (x, y) => new THREE.Vector2((x - OX) * S, (y - OY) * S);
const N = (x, y) => Z(NK * x + NTX, NK * y + NTY);

// Görünüş (şematik) birimi -> metre: 300 cm kat = 171 birim
const GS = 0.017544;

// ---------------------------------------------------------------------------
// 2. Kotlar (şematik görünüş)
// ---------------------------------------------------------------------------
export const KOT = {
  otoparkKati: 0.0,          // OTOPARK KATI ±0.00
  katlar: [3.0, 6.0, 9.0],   // ZEMİN KAT, 1. KAT, 2. KAT (300 cm)
  cati: 12.0,
  parapet: 1.0,              // PARAPET DUVAR 100
  doseme: 0.30,              // görünüşte balkon döşeme kalınlığı
  dukkan: 4.5,               // DÜKKAN BLOĞU 450
  dukkanParapet: 0.9,
  pencereG: 2.0,             // 200/220
  pencereY: 2.2,
  korkuluk: 0.9,             // Alüminyum-Cam Korkuluk 90 cm
  balkonParapet: 0.9,
};

// ---------------------------------------------------------------------------
// 3. Geometri verisi
// ---------------------------------------------------------------------------
// Parsel sınırı (zemin kat planı, dış çizgi)
const PARSEL = [
  [315.6, 680.7], [2949.3, 680.7], [3030.9, 707.0], [3092.4, 785.2],
  [3096.8, 873.8], [2953.2, 1400.1], [2006.6, 1384.9], [1882.4, 1840.2],
  [32.0, 1840.2], [50.6, 1778.1], [160.1, 1411.2],
];
// Komşu cephelerdeki çift çizgi (sınır duvarı) — dış ve iç çizgi
const SINIR_DIS = [[2953.2, 1400.1], [2006.6, 1384.9], [1882.4, 1840.2], [32.0, 1840.2], [50.6, 1778.1], [160.1, 1411.2], [315.6, 680.7]];
const SINIR_IC = [[2956.0, 1389.9], [1998.8, 1374.6], [1874.6, 1830.0], [45.6, 1830.0], [60.3, 1781.0], [170.1, 1413.7], [325.6, 682.8]];

// Otopark katı (zemin kat planı) konut bloğu dış hattı — kuzey ve güneyde
// merdiven/asansör çekirdeği önünde girinti var.
const OTOPARK_KATI = [
  [448.4, 1037.5], [1024.1, 1037.5], [1024.1, 1104.7], [1151.4, 1104.7],
  [1151.4, 1037.5], [1727.2, 1037.5], [1727.2, 1616.0], [1151.4, 1616.0],
  [1151.4, 1492.3], [1024.1, 1492.3], [1024.1, 1616.0], [448.4, 1616.0],
];

// Normal kat dış hattı (balkonlar dahil) — normal kat planı birimi
const NORMAL_DIS = [
  [472.8, 1047.9], [904.7, 1047.9], [904.7, 1099.6], [1057.4, 1099.6],
  [1057.4, 1168.0], [1186.8, 1168.0], [1186.8, 1099.6], [1339.5, 1099.6],
  [1339.5, 1047.9], [1771.4, 1047.9], [1771.4, 1738.9], [1339.5, 1738.9],
  [1339.5, 1687.0], [1186.8, 1687.0], [1186.8, 1561.5], [1057.4, 1561.5],
  [1057.4, 1687.0], [904.7, 1687.0], [904.7, 1738.9], [472.8, 1738.9],
];
// Normal kat kapalı hacim hattı (köşe balkonları hariç)
const NORMAL_KAPALI = [
  [472.8, 1125.6], [702.9, 1125.6], [702.9, 1047.9], [904.7, 1047.9],
  [904.7, 1099.6], [1057.4, 1099.6], [1057.4, 1168.0], [1186.8, 1168.0],
  [1186.8, 1099.6], [1339.5, 1099.6], [1339.5, 1047.9], [1541.3, 1047.9],
  [1541.3, 1125.6], [1771.4, 1125.6], [1771.4, 1661.2], [1541.3, 1661.2],
  [1541.3, 1738.9], [1339.5, 1738.9], [1339.5, 1687.0], [1186.8, 1687.0],
  [1186.8, 1561.5], [1057.4, 1561.5], [1057.4, 1687.0], [904.7, 1687.0],
  [904.7, 1738.9], [702.9, 1738.9], [702.9, 1661.2], [472.8, 1661.2],
];
// Köşe balkonlarının açık kenarları (dolu parapet) — normal kat planı
const BALKON_KENARLARI = [
  [[472.8, 1125.6], [472.8, 1047.9], [702.9, 1047.9]],   // kuzeybatı
  [[1541.3, 1047.9], [1771.4, 1047.9], [1771.4, 1125.6]], // kuzeydoğu
  [[1771.4, 1661.2], [1771.4, 1738.9], [1541.3, 1738.9]], // güneydoğu
  [[702.9, 1738.9], [472.8, 1738.9], [472.8, 1661.2]],   // güneybatı
];
// Pencereler (normal kat planı): [x0, x1, cephe y'si, tip]
//  'f' : oda penceresi 200/220 + 90 cm alüminyum-cam korkuluk + mermer denizlik
//  'b' : salon penceresi 200/220 (balkona açılır)
const PENCERELER = [
  [531.6, 633.3, 1125.6, 'b'], [1610.9, 1712.6, 1125.6, 'b'],
  [756.9, 858.5, 1047.9, 'f'], [1385.7, 1487.3, 1047.9, 'f'],
  [930.9, 1032.5, 1099.6, 'f'], [1211.7, 1313.3, 1099.6, 'f'],
  [531.6, 633.3, 1661.2, 'b'], [1610.9, 1712.6, 1661.2, 'b'],
  [756.9, 858.5, 1738.9, 'f'], [1385.7, 1487.3, 1738.9, 'f'],
  [930.9, 1032.5, 1687.0, 'f'], [1211.7, 1313.3, 1687.0, 'f'],
];

// Dükkan bloğu (zemin kat planı dış hattı)
const DUKKAN = { x0: 1719.6, x1: 2616.3, y0: 935.5, y1: 1230.2 };
// Dükkan vitrini (şematik görünüş birimi). Görünüşte doğu solda.
const VITRIN = {
  doguUcu: 401.7, batiUcu: 1403.8, zemin: 1570.6,
  x0: 430.2, x1: 1375.2, ust: 1342.8,
  dikmeler: [430.2, 487.1, 544.1, 601.1, 658.0, 715.0, 771.9, 828.9, 857.3, 914.3,
    971.2, 1028.2, 1085.2, 1142.1, 1199.1, 1227.5, 1284.5, 1341.4, 1370.0, 1375.2],
  kayitlar: [1371.3, 1399.8, 1428.2, 1456.8, 1485.2, 1513.6, 1542.2],
  kapilar: [[544.1, 601.1], [857.3, 914.3], [1227.5, 1284.5]],
  kapiUst: 1456.8,
};

// Otopark çizgileri (zemin kat planı)
const OTOPARK_YERLERI = (() => {
  const r = [];
  const xs = [524.8, 652.1, 779.6, 907.0, 1034.4, 1161.8, 1289.2, 1416.6, 1544.1, 1671.4];
  for (let i = 0; i < 9; i++) r.push([[xs[i], 680.7], [xs[i + 1], 680.7], [xs[i + 1], 935.5], [xs[i], 935.5]]);
  r.push([[2710.4, 1323.0], [2743.7, 1200.0], [2989.6, 1266.7], [2956.2, 1389.7]]);
  r.push([[2743.8, 1200.1], [2777.2, 1077.1], [3023.2, 1143.8], [2989.8, 1266.8]]);
  r.push([[2777.3, 1077.1], [2810.7, 954.2], [3056.7, 1020.8], [3023.3, 1143.8]]);
  r.push([[2810.9, 954.2], [2844.3, 831.2], [3090.2, 897.9], [3056.8, 1020.9]]);
  return r;
})();

// ---------------------------------------------------------------------------
// 4. Malzemeler
// ---------------------------------------------------------------------------
function malzemeler(mod) {
  const std = (color, roughness = 0.85, metalness = 0, extra = {}) =>
    new THREE.MeshStandardMaterial({ color, roughness, metalness, envMapIntensity: 0.5, ...extra });
  const m = {
    duvar: std(0xf3f1ec, 0.82),
    cati: std(0xbdb9b1, 0.95),
    alu: std(0x8e959c, 0.32, 0.75, { envMapIntensity: 1.0 }),
    mermer: std(0xebe7df, 0.35),
    cam: new THREE.MeshPhysicalMaterial({ color: 0x31434f, roughness: 0.04, metalness: 0.55, envMapIntensity: 1.25, clearcoat: 1, clearcoatRoughness: 0.03 }),
    korkulukCam: new THREE.MeshPhysicalMaterial({ color: 0x9fc2cc, roughness: 0.05, metalness: 0.35, transparent: true, opacity: 0.5, depthWrite: false, envMapIntensity: 1.4 }),
    zemin: std(0xd9d3c7, 0.97),
    asfalt: std(0x6a6d71, 0.96),
    maket: std(0xeceae5, 0.98),
    sinir: std(0xb2aa9c, 0.9),
    cizgi: std(0xffffff, 0.7),
    girinti: std(0xe4e1da, 0.85),
  };
  if (mod === 'diyagram') {
    m.konut = std(0xf2d49b, 0.8);
    m.otopark = std(0xa9b8c6, 0.85);
    m.dukkan = std(0xe0876a, 0.8);
    m.cati = std(0xd9d2c4, 0.95);
  } else {
    m.konut = m.duvar; m.otopark = m.duvar; m.dukkan = m.duvar;
  }
  return m;
}

// ---------------------------------------------------------------------------
// 5. Yardımcı geometri fonksiyonları
// ---------------------------------------------------------------------------
function golge(o, cast = true, receive = true) { o.castShadow = cast; o.receiveShadow = receive; return o; }

// Yatay çokgeni y0..y1 arasında yükselt
function yukselt(pts, y0, y1, mat) {
  const sh = new THREE.Shape(pts.map(p => new THREE.Vector2(p.x, -p.y)));
  const g = new THREE.ExtrudeGeometry(sh, { depth: y1 - y0, bevelEnabled: false });
  g.rotateX(-Math.PI / 2); g.translate(0, y0, 0);
  return golge(new THREE.Mesh(g, mat));
}

// Dik açılı çokgenin içine doğru t kalınlığında halka (parapet)
function halka(pts, t, y0, y1, mat) {
  const A = isaretliAlan(pts), n = pts.length;
  const ic = pts.map((v, i) => {
    const a = pts[(i - 1 + n) % n], b = pts[(i + 1) % n];
    const n1 = icNormal(a, v, A), n2 = icNormal(v, b, A);
    return v.clone().addScaledVector(n1, t).addScaledVector(n2, t);
  });
  const sh = new THREE.Shape(pts.map(p => new THREE.Vector2(p.x, -p.y)));
  sh.holes.push(new THREE.Path(ic.map(p => new THREE.Vector2(p.x, -p.y))));
  const g = new THREE.ExtrudeGeometry(sh, { depth: y1 - y0, bevelEnabled: false });
  g.rotateX(-Math.PI / 2); g.translate(0, y0, 0);
  return golge(new THREE.Mesh(g, mat));
}

// İki dünya noktası arasında kutu (yatay eksen a->b, kalınlık t, iç yön n)
function kutuKenar(a, b, y0, y1, t, nIc, mat, disTasma = 0) {
  const d = new THREE.Vector2().subVectors(b, a); const L = d.length(); d.normalize();
  const g = new THREE.BoxGeometry(L, y1 - y0, t);
  const m = new THREE.Mesh(g, mat);
  const mid = new THREE.Vector2().addVectors(a, b).multiplyScalar(0.5)
    .addScaledVector(nIc, t / 2 - disTasma);
  m.position.set(mid.x, (y0 + y1) / 2, mid.y);
  m.rotation.y = -Math.atan2(d.y, d.x);
  return golge(m);
}

function isaretliAlan(pts) {
  let A = 0; for (let i = 0; i < pts.length; i++) { const p = pts[i], q = pts[(i + 1) % pts.length]; A += p.x * q.y - q.x * p.y; }
  return A / 2;
}
// Kenarın iç yöne bakan normali (çokgen yönüne göre)
function icNormal(a, b, alan) {
  const d = new THREE.Vector2().subVectors(b, a).normalize();
  // X doğu / Z güney düzleminde
  const n = alan > 0 ? new THREE.Vector2(-d.y, d.x) : new THREE.Vector2(d.y, -d.x);
  return n;
}

// Boşluklu duvar paneli: a->b kenarı boyunca, dıştan içe t kalınlığında
function bosukluDuvar(a, b, y0, y1, t, nIc, bosluklar, mat) {
  const d = new THREE.Vector2().subVectors(b, a); const L = d.length(); d.normalize();
  const sh = new THREE.Shape();
  sh.moveTo(0, y0); sh.lineTo(L, y0); sh.lineTo(L, y1); sh.lineTo(0, y1); sh.lineTo(0, y0);
  for (const [u0, u1, v0, v1] of bosluklar) {
    const h = new THREE.Path();
    h.moveTo(u0, v0); h.lineTo(u0, v1); h.lineTo(u1, v1); h.lineTo(u1, v0); h.lineTo(u0, v0);
    sh.holes.push(h);
  }
  const g = new THREE.ExtrudeGeometry(sh, { depth: t, bevelEnabled: false });
  // yerel eksenler: ex = kenar yönü, ey = yukarı, ez = ex × ey
  const ex = new THREE.Vector3(d.x, 0, d.y), ey = new THREE.Vector3(0, 1, 0);
  const ez = new THREE.Vector3().crossVectors(ex, ey);
  const nIc3 = new THREE.Vector3(nIc.x, 0, nIc.y);
  const o = new THREE.Vector3(a.x, 0, a.y);
  if (ez.dot(nIc3) < 0) o.addScaledVector(nIc3, t); // ez dışa bakıyorsa içten başla
  const M = new THREE.Matrix4().makeBasis(ex, ey, ez).setPosition(o);
  g.applyMatrix4(M);
  return golge(new THREE.Mesh(g, mat));
}

// ---------------------------------------------------------------------------
// 6. Bina parçaları
// ---------------------------------------------------------------------------
function pencere(grup, m, merkez, d, nDis, taban, tip) {
  // merkez: cephe üzerindeki pencere orta noktası (dünya XZ), d: cephe yönü
  const W = KOT.pencereG, Hh = KOT.pencereY, cekme = 0.12, prof = 0.06;
  const ang = -Math.atan2(d.y, d.x);
  const yer = (u, ofs) => new THREE.Vector3(merkez.x + d.x * u + nDis.x * ofs, 0, merkez.y + d.y * u + nDis.y * ofs);
  const parca = (w, h, dz, u, v, ofs, mat) => {
    const b = golge(new THREE.Mesh(new THREE.BoxGeometry(w, h, dz), mat), true, true);
    const p = yer(u, ofs); b.position.set(p.x, v, p.z); b.rotation.y = ang; grup.add(b); return b;
  };
  // cam
  parca(W, Hh, 0.02, 0, taban + Hh / 2, -cekme, m.cam);
  // alüminyum kasa + orta kayıt (sürme iki kanat)
  parca(W, prof, 0.07, 0, taban + Hh - prof / 2, -cekme + 0.01, m.alu);
  parca(W, prof, 0.07, 0, taban + prof / 2, -cekme + 0.01, m.alu);
  parca(prof, Hh, 0.07, -W / 2 + prof / 2, taban + Hh / 2, -cekme + 0.01, m.alu);
  parca(prof, Hh, 0.07, W / 2 - prof / 2, taban + Hh / 2, -cekme + 0.01, m.alu);
  parca(0.08, Hh, 0.07, 0, taban + Hh / 2, -cekme + 0.02, m.alu);
  if (tip === 'f') {
    // 3 cm mermer denizlik
    parca(W + 0.3, 0.03, 0.26, 0, taban + 0.015, 0.0, m.mermer);
    // 90 cm alüminyum-cam korkuluk (temperli reflekte cam)
    const kH = KOT.korkuluk, o = 0.08;
    parca(W - 0.06, kH - 0.08, 0.016, 0, taban + 0.03 + (kH - 0.08) / 2, o, m.korkulukCam);
    parca(W, 0.05, 0.05, 0, taban + kH - 0.025, o, m.alu);
    parca(W, 0.03, 0.04, 0, taban + 0.045, o, m.alu);
    parca(0.04, kH, 0.04, -W / 2 + 0.02, taban + kH / 2, o, m.alu);
    parca(0.04, kH, 0.04, W / 2 - 0.02, taban + kH / 2, o, m.alu);
  }
}

function konutBlogu(m) {
  const g = new THREE.Group(); g.name = 'konut';
  const t = 0.25;

  // Otopark katı (±0.00 – +3.00)
  const ok = OTOPARK_KATI.map(p => Z(...p));
  const okMesh = yukselt(ok, 0, KOT.katlar[0] - KOT.doseme, m.otopark); okMesh.name = 'otoparkKati';
  g.add(okMesh);

  // Normal katlar: döşemeler (balkonlar dahil) ve çatı döşemesi
  const dis = NORMAL_DIS.map(p => N(...p));
  for (const k of [...KOT.katlar, KOT.cati]) g.add(yukselt(dis, k - KOT.doseme, k - (k === KOT.cati ? 0.02 : 0), m.konut));
  // çatı üst yüzeyi (yalıtım/kaplama tonu); alt yüzü duvar renginde kalsın diye ayrı katman
  g.add(golge(yukselt(dis, KOT.cati - 0.02, KOT.cati, m.cati), false, true));

  // Kapalı hacim duvarları (pencere boşluklu)
  const kap = NORMAL_KAPALI.map(p => N(...p));
  const A = isaretliAlan(kap);
  for (let i = 0; i < NORMAL_KAPALI.length; i++) {
    const pa = NORMAL_KAPALI[i], pb = NORMAL_KAPALI[(i + 1) % NORMAL_KAPALI.length];
    const a = kap[i], b = kap[(i + 1) % kap.length];
    const nIc = icNormal(a, b, A), nDis = nIc.clone().negate();
    const d = new THREE.Vector2().subVectors(b, a); const L = d.length(); d.normalize();
    const bosluklar = [];
    if (Math.abs(pa[1] - pb[1]) < 0.5) {
      for (const [x0, x1, y, tip] of PENCERELER) {
        if (Math.abs(y - pa[1]) > 0.5) continue;
        const lo = Math.min(pa[0], pb[0]), hi = Math.max(pa[0], pb[0]);
        if (x0 < lo || x1 > hi) continue;
        const c = N((x0 + x1) / 2, y);
        const u = new THREE.Vector2().subVectors(c, a).dot(d);
        for (const k of KOT.katlar) {
          bosluklar.push([u - KOT.pencereG / 2, u + KOT.pencereG / 2, k, k + KOT.pencereY]);
          pencere(g, m, c, d, nDis, k, tip);
        }
      }
    }
    g.add(bosukluDuvar(a, b, KOT.katlar[0], KOT.cati, t, nIc, bosluklar, m.konut));
  }

  // Balkon parapetleri (dolu, 90 cm)
  const pt = 0.15;
  for (const kenar of BALKON_KENARLARI) {
    const q = kenar.map(p => N(...p));
    // balkonun iç tarafını bulmak için kapalı hatta göre: balkon dikdörtgeninin merkezi
    const mx = (q[0].x + q[2].x) / 2, mz = (q[0].y + q[2].y) / 2;
    for (let i = 0; i < 2; i++) {
      const a = q[i], b = q[i + 1];
      const mid = new THREE.Vector2().addVectors(a, b).multiplyScalar(0.5);
      const nIc = new THREE.Vector2(mx - mid.x, mz - mid.y);
      // eksene hizala
      if (Math.abs(nIc.x) > Math.abs(nIc.y)) nIc.set(Math.sign(nIc.x), 0); else nIc.set(0, Math.sign(nIc.y));
      for (const k of KOT.katlar) g.add(kutuKenar(a, b, k, k + KOT.balkonParapet, pt, nIc, m.konut));
    }
  }

  // Çatı parapeti (100 cm) — dış hat boyunca 20 cm kalınlıkta halka
  g.add(halka(dis, 0.2, KOT.cati, KOT.cati + KOT.parapet, m.konut));
  return g;
}

function dukkanBlogu(m) {
  const g = new THREE.Group(); g.name = 'dukkan';
  const { x0, x1, y0, y1 } = DUKKAN;
  const H = KOT.dukkan, t = 0.25;
  const p = [Z(x0, y0), Z(x1, y0), Z(x1, y1), Z(x0, y1)];
  const A = isaretliAlan(p);
  // vitrin: görünüş -> plan
  const gx = xe => x0 + (VITRIN.batiUcu - xe) * GS / S; // görünüş x -> zemin planı x
  const gy = ye => (VITRIN.zemin - ye) * GS;           // görünüş y -> kot
  for (let i = 0; i < 4; i++) {
    const a = p[i], b = p[(i + 1) % 4];
    const nIc = icNormal(a, b, A);
    let bosluk = [];
    if (i === 0) { // kuzey cephe (706. Sokak) — vitrin
      const d = new THREE.Vector2().subVectors(b, a).normalize();
      const u0 = Z(gx(VITRIN.x1), y0).sub(a).dot(d), u1 = Z(gx(VITRIN.x0), y0).sub(a).dot(d);
      bosluk = [[u0, u1, 0, gy(VITRIN.ust)]];
    }
    g.add(bosukluDuvar(a, b, 0, H, t, nIc, bosluk, m.dukkan));
  }
  g.add(yukselt(p, H - KOT.doseme, H - 0.02, m.dukkan));
  g.add(golge(yukselt(p, H - 0.02, H, m.cati), false, true));
  // parapet 90 cm
  g.add(halka(p, 0.2, H, H + KOT.dukkanParapet, m.dukkan));
  // vitrin camı ve alüminyum doğrama ızgarası
  const cy = Z(0, y0).y; // cephe Z
  const cekme = 0.12;
  const zc = cy + cekme; // cephe içine
  const vx0 = Z(gx(VITRIN.x1), 0).x, vx1 = Z(gx(VITRIN.x0), 0).x, vH = gy(VITRIN.ust);
  const cam = golge(new THREE.Mesh(new THREE.BoxGeometry(vx1 - vx0, vH, 0.02), m.cam));
  cam.position.set((vx0 + vx1) / 2, vH / 2, zc); g.add(cam);
  const pr = 0.06;
  const dikme = (x, yA, yB) => { const b = golge(new THREE.Mesh(new THREE.BoxGeometry(pr, yB - yA, 0.08), m.alu)); b.position.set(x, (yA + yB) / 2, zc - 0.02); g.add(b); };
  const kayit = (xa, xb, y) => { const b = golge(new THREE.Mesh(new THREE.BoxGeometry(Math.abs(xb - xa), pr, 0.08), m.alu)); b.position.set((xa + xb) / 2, y, zc - 0.02); g.add(b); };
  for (const xe of VITRIN.dikmeler) dikme(Z(gx(xe), 0).x, 0, vH);
  kayit(vx0, vx1, vH - pr / 2); kayit(vx0, vx1, pr / 2);
  const kapiUst = gy(VITRIN.kapiUst);
  for (const ye of VITRIN.kayitlar) {
    const y = gy(ye);
    if (y > kapiUst + 0.01) { kayit(vx0, vx1, y); continue; }
    if (Math.abs(y - kapiUst) < 0.01) { kayit(vx0, vx1, y); continue; }
    // kapı hizasında kesilir
    let segs = [[VITRIN.x0, VITRIN.x1]];
    for (const [k0, k1] of VITRIN.kapilar) {
      const n = [];
      for (const [s0, s1] of segs) { if (k1 <= s0 || k0 >= s1) n.push([s0, s1]); else { if (k0 > s0) n.push([s0, k0]); if (k1 < s1) n.push([k1, s1]); } }
      segs = n;
    }
    for (const [s0, s1] of segs) kayit(Z(gx(s1), 0).x, Z(gx(s0), 0).x, y);
  }
  return g;
}

// ---------------------------------------------------------------------------
// 7. Arsa ve çevre (yalnızca çizimdekiler)
// ---------------------------------------------------------------------------
function metinDokusu(metin, w = 2048, h = 256, renk = 'rgba(255,255,255,0.92)') {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const x = c.getContext('2d');
  let px = Math.round(h * 0.62);
  const ayarla = () => {
    x.font = `600 ${px}px "DejaVu Sans", "Liberation Sans", Arial, sans-serif`;
    if ('letterSpacing' in x) x.letterSpacing = `${Math.round(px * 0.2)}px`;
  };
  ayarla();
  while (x.measureText && x.measureText(metin).width > w * 0.92 && px > 20) { px -= 4; ayarla(); }
  x.fillStyle = renk; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.fillText(metin, w / 2, h / 2 + h * 0.03);
  const t = new THREE.CanvasTexture(c); t.anisotropy = 8; t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export const MAKET = { x0: -42, x1: 42, z0: -24, z1: 24, kalinlik: 0.02 };

function arsa(m) {
  const g = new THREE.Group(); g.name = 'arsa';
  const { x0, x1, z0, z1, kalinlik } = MAKET;

  // maket tablası
  const tabla = golge(new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, kalinlik, z1 - z0), m.maket), false, true);
  tabla.position.set((x0 + x1) / 2, -kalinlik / 2 - 0.001, (z0 + z1) / 2); g.add(tabla);

  // yollar: 706. Sokak (kuzey) ve Odunluk Caddesi (doğu) — parsel sınırına kadar
  const pr = PARSEL.map(p => Z(...p));
  const E = pr[4], F = pr[5];
  const dir = new THREE.Vector2().subVectors(F, E).normalize();
  const tGuney = (z1 - F.y) / dir.y;
  const Fg = F.clone().addScaledVector(dir, tGuney);
  const yol = [
    new THREE.Vector2(x0, z0), new THREE.Vector2(x1, z0), new THREE.Vector2(x1, z1), Fg,
    F, E, pr[3], pr[2], pr[1], pr[0], new THREE.Vector2(x0, pr[0].y),
  ];
  g.add(golge(yukselt(yol, 0, 0.012, m.asfalt), false, true));

  // parsel zemini
  g.add(golge(yukselt(pr, 0, 0.02, m.zemin), false, true));

  // komşu sınırındaki çift çizgi (sınır duvarı hattı)
  const dis = SINIR_DIS.map(p => Z(...p)), ic = SINIR_IC.map(p => Z(...p));
  for (let i = 0; i < dis.length - 1; i++) {
    const q = [dis[i], dis[i + 1], ic[i + 1], ic[i]];
    if (isaretliAlan(q) < 0) q.reverse();
    g.add(golge(yukselt(q, 0.02, 0.06, m.sinir), false, true));
  }

  // otopark çizgileri
  const cw = 0.1;
  for (const yer of OTOPARK_YERLERI) {
    const q = yer.map(p => Z(...p));
    for (let i = 0; i < 4; i++) {
      const a = q[i], b = q[(i + 1) % 4];
      const d = new THREE.Vector2().subVectors(b, a); const L = d.length(); d.normalize();
      const bx = golge(new THREE.Mesh(new THREE.BoxGeometry(L + cw, 0.01, cw), m.cizgi), false, true);
      bx.position.set((a.x + b.x) / 2, 0.026, (a.y + b.y) / 2); bx.rotation.y = -Math.atan2(d.y, d.x);
      g.add(bx);
    }
  }

  // sokak adları (plandaki gibi)
  const yazi = (metin, x, z, aci, en) => {
    const tex = metinDokusu(metin);
    const pl = new THREE.Mesh(new THREE.PlaneGeometry(en, en / 8), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, toneMapped: false, opacity: 0.85 }));
    pl.geometry.rotateX(-Math.PI / 2);
    pl.position.set(x, 0.03, z); pl.rotation.y = aci; pl.renderOrder = 2;
    pl.userData.yaziAci = aci; pl.name = 'yazi';
    g.add(pl);
  };
  yazi('706. SOKAK', -4, (z0 + pr[0].y) / 2, 0, 15);
  const nE = new THREE.Vector2(-dir.y, dir.x); if (nE.x < 0) nE.negate();
  const orta = new THREE.Vector2().addVectors(E, F).multiplyScalar(0.5).addScaledVector(nE, 5.2).addScaledVector(dir, 4);
  // yazı F->E yönünde (plandaki gibi aşağıdan yukarı) okunur
  yazi('ODUNLUK CADDESİ', orta.x, orta.y, Math.atan2(dir.y, -dir.x), 19);
  return g;
}

// ---------------------------------------------------------------------------
// 8. Sahne
// ---------------------------------------------------------------------------
export function sahneKur(mod = 'render') {
  const m = malzemeler(mod);
  const kok = new THREE.Group();
  kok.add(arsa(m));
  kok.add(konutBlogu(m));
  kok.add(dukkanBlogu(m));
  return { kok, m };
}

// Kat etiketleri için referans noktalar (diyagram)
export function etiketNoktalari() {
  const ust = N(472.8, 1738.9), alt = Z(448.4, 1616.0); // güneybatı köşeleri
  return {
    katlar: [
      { ad: 'OTOPARK KATI', kot: '±0.00', y: 1.5, nokta: alt },
      { ad: 'ZEMİN KAT', kot: '+3.00', y: 4.5, nokta: ust },
      { ad: '1. KAT', kot: '+6.00', y: 7.5, nokta: ust },
      { ad: '2. KAT', kot: '+9.00', y: 10.5, nokta: ust },
    ],
    dukkan: Z((DUKKAN.x0 + DUKKAN.x1) / 2, (DUKKAN.y0 + DUKKAN.y1) / 2),
  };
}

export const MERKEZ = { konut: N(1122, 1393), dukkan: Z(2168, 1083) };
