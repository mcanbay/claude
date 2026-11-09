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
  kat: 3.0,
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
  } else if (mod === 'tasarim') {
    // Cephe tasarımı: açık doğal tonlu sıva + antrasit / koyu gri / ahşap tonlu kompozit
    m.siva = std(0xe9e4da, 0.88);
    m.antrasit = std(0x363b3f, 0.42, 0.35);
    m.koyugri = std(0x555b5f, 0.4, 0.35);
    m.ahsap = std(0x9c6b43, 0.62);
    m.derz = std(0x141618, 0.8);
    m.alu = std(0x2c3034, 0.35, 0.7, { envMapIntensity: 1.0 }); // antrasit metal doğrama/profil
    m.icDuvar = std(0xd8d1c5, 0.9);
    m.kapiCam = std(0x161a1d, 0.06, 0.2, { envMapIntensity: 1.2 });
    m.korkulukCam = new THREE.MeshPhysicalMaterial({ color: 0xb9d3d6, roughness: 0.04, metalness: 0.2, transparent: true, opacity: 0.32, depthWrite: false, envMapIntensity: 1.4 });
    m.konut = m.siva; m.otopark = m.siva; m.dukkan = m.siva; m.duvar = m.siva;
  } else {
    m.konut = m.duvar; m.otopark = m.duvar; m.dukkan = m.duvar;
  }
  // Blender'da malzeme eşlemesi için adlar
  for (const [k, v] of Object.entries(m)) if (!v.name) v.name = k;
  if (m.siva) m.siva.name = 'siva';
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
  const dis2 = pts.map(p => new THREE.Vector2(p.x, -p.y));
  let ic2 = ic.map(p => new THREE.Vector2(p.x, -p.y));
  // three.js dış kontur saat yönündeyse deliği çevirmez: iç yüzlerin normalleri
  // doğru (içe bakan) olsun diye delik her zaman dış konturun tersi yönde verilir
  if (THREE.ShapeUtils.isClockWise(dis2) === THREE.ShapeUtils.isClockWise(ic2)) ic2 = ic2.reverse();
  const sh = new THREE.Shape(dis2);
  sh.holes.push(new THREE.Path(ic2));
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

// i. köşe dış (dışbükey) köşe mi?
function disKose(pts, i, alan) {
  const n = pts.length, a = pts[(i - 1 + n) % n], v = pts[i], b = pts[(i + 1) % n];
  const cr = (v.x - a.x) * (b.y - v.y) - (v.y - a.y) * (b.x - v.x);
  return Math.sign(cr) === Math.sign(alan);
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
  // köşelerde parçalar üst üste binmez (eş düzlem yüz bırakmamak için)
  parca(prof, Hh - 2 * prof, 0.07, -W / 2 + prof / 2, taban + Hh / 2, -cekme + 0.01, m.alu);
  parca(prof, Hh - 2 * prof, 0.07, W / 2 - prof / 2, taban + Hh / 2, -cekme + 0.01, m.alu);
  parca(0.08, Hh - 2 * prof, 0.07, 0, taban + Hh / 2, -cekme + 0.02, m.alu);
  if (tip === 'f') {
    // 3 cm mermer denizlik
    parca(W + 0.3, 0.03, 0.26, 0, taban + 0.015, 0.0, m.mermer);
    // 90 cm alüminyum-cam korkuluk (temperli reflekte cam)
    const kH = KOT.korkuluk, o = 0.08;
    parca(W - 0.06, kH - 0.08, 0.016, 0, taban + 0.03 + (kH - 0.08) / 2, o, m.korkulukCam);
    parca(W, 0.05, 0.05, 0, taban + kH - 0.025, o, m.alu);
    parca(W, 0.03, 0.04, 0, taban + 0.045, o, m.alu);
    parca(0.04, kH - 0.11, 0.04, -W / 2 + 0.02, taban + 0.06 + (kH - 0.11) / 2, o, m.alu);
    parca(0.04, kH - 0.11, 0.04, W / 2 - 0.02, taban + 0.06 + (kH - 0.11) / 2, o, m.alu);
  }
}

function konutBlogu(m, mod) {
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
    // Duvarlar kat kat (döşeme araları) ve dış köşede kalınlık kadar kısaltılarak
    // üretilir: aynı düzlemde çakışan yüz kalmaz (yol izlemeli render'da siyah leke yapar)
    const bK = disKose(kap, (i + 1) % kap.length, A) ? b.clone().addScaledVector(d, -t) : b;
    for (const k of KOT.katlar) {
      const ust = k + KOT.kat - KOT.doseme;
      g.add(bosukluDuvar(a, bK, k, ust, t, nIc, bosluklar.filter(h => h[2] >= k && h[3] <= ust), m.konut));
    }
  }

  // Balkon parapetleri (dolu, 90 cm) — tasarım modunda cam korkuluk kullanılır (cephe())
  const pt = 0.15;
  for (const kenar of (mod === 'tasarim' ? [] : BALKON_KENARLARI)) {
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
    const bK = b.clone().addScaledVector(new THREE.Vector2().subVectors(b, a).normalize(), -t); // dikdörtgen: tüm köşeler dış köşe
    g.add(bosukluDuvar(a, bK, 0, H - KOT.doseme, t, nIc, bosluk, m.dukkan));
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
  const kayit = (xa, xb, y) => { const b = golge(new THREE.Mesh(new THREE.BoxGeometry(Math.abs(xb - xa), pr, 0.07), m.alu)); b.position.set((xa + xb) / 2, y, zc - 0.02); g.add(b); };
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
// 6b. Cephe tasarımı (malzeme kompozisyonu) — kütle, pencere ve balkon düzeni
//     çizimdeki gibi kalır; kaplamalar duvar yüzeyinin önüne giydirilir.
//   • Çıkmalı kanatlar (köşe balkonu + 8,91 m² oda kutusu): açık tonlu dekoratif sıva
//   • Geri çekilmiş orta akslar (13,18 m² oda pencereleri): koyu gri kompozit panel
//   • Boşluklar (merdiven yarığı / bina girişi, balkon cepleri): ahşap tonlu kompozit
//   • Otopark katı kaidesi ve dükkan: antrasit kompozit
//   • Doğrama, korkuluk profilleri, harpuşta: antrasit metal; balkonlarda cam korkuluk
// ---------------------------------------------------------------------------
const KAPLAMA = { ofs: 0.03, kal: 0.02, derz: 0.012 };

// [0, L] aralığını sabit noktalarda bölüp her parçayı ~modül genişliğinde eşit böl
function bolum(L, sabit, modul) {
  const s = [...new Set([0, L, ...sabit.filter(u => u > 0.02 && u < L - 0.02)])].sort((a, b) => a - b);
  const out = [];
  for (let i = 0; i < s.length - 1; i++) {
    const a = s[i], b = s[i + 1], n = Math.max(1, Math.round((b - a) / modul));
    for (let k = 0; k < n; k++) out.push(a + (b - a) * k / n);
  }
  out.push(L);
  return out;
}

function kutuYerlestir(mesh, merkez, ex, ey, ez) {
  mesh.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(ex, ey, ez));
  mesh.position.copy(merkez);
  return golge(mesh);
}

// Düşey cephe yüzeyine panel / lambri kaplama
//  a,b: duvar dış yüzü çizgisi (dünya XZ), nDis: dış normal, y0..y1 kot aralığı
//  bosluk: [u0,u1,v0,v1] pencere/kapı boşlukları, modul: panel genişliği
function kaplama(g, m, { a, b, nDis, y0, y1, bosluk = [], modul = 1.2, vKes = [], mat, lambri = false, pervaz = true, uzat = [0, 0] }) {
  const { ofs, kal, derz } = KAPLAMA;
  // dış köşede panel köşeyi sarsın diye yüzey uçlarından uzatılabilir (uzat: [baş, son])
  if (uzat[0] || uzat[1]) {
    const e = new THREE.Vector2().subVectors(b, a).normalize();
    bosluk = bosluk.map(([u0, u1, v0, v1]) => [u0 + uzat[0], u1 + uzat[0], v0, v1]);
    a = a.clone().addScaledVector(e, -uzat[0]); b = b.clone().addScaledVector(e, uzat[1]);
  }
  const d = new THREE.Vector2().subVectors(b, a); const L = d.length(); d.normalize();
  const n3 = new THREE.Vector3(nDis.x, 0, nDis.y), d3 = new THREE.Vector3(d.x, 0, d.y), up = new THREE.Vector3(0, 1, 0);
  // sağ el sistemi: ex=d3, ey=up, ez=ex×ey (dış ya da iç normal olabilir; kutu simetrik)
  const ez = new THREE.Vector3().crossVectors(d3, up);
  const uKes = bolum(L, bosluk.flatMap(h => [h[0], h[1]]), modul);
  const vs = [...new Set([y0, y1, ...vKes, ...bosluk.flatMap(h => [h[2], h[3]])].filter(v => v >= y0 - 1e-6 && v <= y1 + 1e-6))].sort((p, q) => p - q);
  const icinde = (u, v) => bosluk.some(([u0, u1, v0, v1]) => u > u0 && u < u1 && v > v0 && v < v1);
  for (let i = 0; i < uKes.length - 1; i++) {
    for (let j = 0; j < vs.length - 1; j++) {
      const u0 = uKes[i], u1 = uKes[i + 1], v0 = vs[j], v1 = vs[j + 1];
      if (u1 - u0 < 0.03 || v1 - v0 < 0.03) continue;
      const uc = (u0 + u1) / 2, vc = (v0 + v1) / 2;
      if (icinde(uc, vc)) continue;
      const pan = new THREE.Mesh(new THREE.BoxGeometry(u1 - u0 - derz, v1 - v0 - derz, kal), mat);
      const c = new THREE.Vector3(a.x + d.x * uc + nDis.x * (ofs + kal / 2), vc, a.y + d.y * uc + nDis.y * (ofs + kal / 2));
      g.add(kutuYerlestir(pan, c, d3, up, ez));
    }
  }
  // arka zemin (derz görünümü için koyu) — duvar yüzü ile panel arası
  const aO = a.clone().addScaledVector(nDis, ofs), bO = b.clone().addScaledVector(nDis, ofs);
  g.add(bosukluDuvar(aO, bO, y0, y1, ofs, nDis.clone().negate(), bosluk, m.derz));
  // pencere/kapı içlikleri (söve): kaplama malzemesiyle camın önüne kadar
  if (pervaz) for (const [u0, u1, v0, v1] of bosluk) {
    const D = ofs + kal + 0.11, t = 0.02, mid = ofs + kal - D / 2;
    const parca = (w, h, uc, vc) => {
      const p = new THREE.Mesh(new THREE.BoxGeometry(w, h, D), mat);
      const c = new THREE.Vector3(a.x + d.x * uc + nDis.x * mid, vc, a.y + d.y * uc + nDis.y * mid);
      g.add(kutuYerlestir(p, c, d3, up, ez));
    };
    parca(u1 - u0, t, (u0 + u1) / 2, v1 - t / 2);
    parca(t, v1 - v0 - t, u0 + t / 2, (v0 + v1 - t) / 2);
    parca(t, v1 - v0 - t, u1 - t / 2, (v0 + v1 - t) / 2);
  }
}

// Balkon tavanı (alt yüz) ahşap lambri: dikdörtgen [p0,p1] (dünya XZ köşeleri), kot y
function tavanLambri(g, m, p0, p1, y, mat) {
  const x0 = Math.min(p0.x, p1.x), x1 = Math.max(p0.x, p1.x), z0 = Math.min(p0.y, p1.y), z1 = Math.max(p0.y, p1.y);
  const { ofs, kal, derz } = KAPLAMA;
  const zs = bolum(z1 - z0, [], 0.2);
  const ex = new THREE.Vector3(0, 0, 1), ey = new THREE.Vector3(1, 0, 0), ez = new THREE.Vector3(0, 1, 0); // uzun eksen (yerel Y) X boyunca
  for (let i = 0; i < zs.length - 1; i++) {
    const w = zs[i + 1] - zs[i];
    const p = new THREE.Mesh(new THREE.BoxGeometry(w - derz, x1 - x0 - 0.01, kal), mat);
    g.add(kutuYerlestir(p, new THREE.Vector3((x0 + x1) / 2, y - ofs - kal / 2, z0 + zs[i] + w / 2), ex, ey, ez));
  }
  const arka = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, ofs, z1 - z0), m.derz);
  arka.position.set((x0 + x1) / 2, y - ofs / 2, (z0 + z1) / 2); g.add(golge(arka));
}

// Çerçevesiz cam korkuluk: alt profil + cam + küpeşte (antrasit)
function camKorkuluk(g, m, a, b, nIc, taban, H = KOT.korkuluk, kisalt = [0, 0]) {
  { const e = new THREE.Vector2().subVectors(b, a).normalize(); a = a.clone().addScaledVector(e, kisalt[0]); b = b.clone().addScaledVector(e, -kisalt[1]); }
  const d = new THREE.Vector2().subVectors(b, a); const L = d.length(); d.normalize();
  const d3 = new THREE.Vector3(d.x, 0, d.y), up = new THREE.Vector3(0, 1, 0), ez = new THREE.Vector3().crossVectors(d3, up);
  const at = (ofs, y, w, h, dz, mat) => {
    const p = new THREE.Mesh(new THREE.BoxGeometry(w, h, dz), mat);
    const mid = new THREE.Vector2().addVectors(a, b).multiplyScalar(0.5).addScaledVector(nIc, ofs);
    g.add(kutuYerlestir(p, new THREE.Vector3(mid.x, y, mid.y), d3, up, ez));
  };
  at(0.07, taban + 0.05, L, 0.10, 0.07, m.alu);                    // alt U profil
  at(0.07, taban + 0.10 + (H - 0.14) / 2, L - 0.02, H - 0.14, 0.017, m.korkulukCam);
  at(0.07, taban + H - 0.02, L, 0.04, 0.05, m.alu);                // küpeşte
}

function disOfset(pts, t) { // dik açılı çokgeni t kadar dışa kaydır
  const A = isaretliAlan(pts), n = pts.length;
  return pts.map((v, i) => {
    const a = pts[(i - 1 + n) % n], b = pts[(i + 1) % n];
    return v.clone().addScaledVector(icNormal(a, v, A), -t).addScaledVector(icNormal(v, b, A), -t);
  });
}

function cephe(m) {
  const g = new THREE.Group(); g.name = 'cephe';
  const KUZEY = new THREE.Vector2(0, -1), GUNEY = new THREE.Vector2(0, 1), DOGU = new THREE.Vector2(1, 0), BATI = new THREE.Vector2(-1, 0);
  const ust = KOT.cati + KOT.parapet;
  const pencereBoslugu = (a, b, x0, x1, y, katlar = KOT.katlar) => {
    const d = new THREE.Vector2().subVectors(b, a).normalize();
    const uc = N((x0 + x1) / 2, y).sub(a).dot(d);
    return katlar.map(k => [uc - KOT.pencereG / 2, uc + KOT.pencereG / 2, k, k + KOT.pencereY]);
  };

  // 1) Geri çekilmiş orta akslar — koyu gri kompozit (+2.70 … parapet üstü)
  for (const [x0, x1, y, n, wx0, wx1] of [
    [904.7, 1057.4, 1099.6, KUZEY, 930.9, 1032.5], [1186.8, 1339.5, 1099.6, KUZEY, 1211.7, 1313.3],
    [904.7, 1057.4, 1687.0, GUNEY, 930.9, 1032.5], [1186.8, 1339.5, 1687.0, GUNEY, 1211.7, 1313.3],
  ]) {
    const a = N(x0, y), b = N(x1, y);
    kaplama(g, m, { a, b, nDis: n, y0: KOT.katlar[0] - KOT.doseme, y1: ust, bosluk: pencereBoslugu(a, b, wx0, wx1, y), modul: 1.0, vKes: [...KOT.katlar, KOT.cati], mat: m.koyugri });
  }

  // 1b) Yan cepheler (doğu/batı sağır duvarlar): ortadaki kat holü aksında aynı genişlikte
  //     koyu gri bant — uzun cephelerdeki koyu orta aksın yan yüzlerdeki karşılığı
  {
    const yarim = (1339.5 - 1186.8) / 2, yc = 1393.4;
    for (const [x, n] of [[472.8, BATI], [1771.4, DOGU]]) {
      kaplama(g, m, { a: N(x, yc - yarim), b: N(x, yc + yarim), nDis: n, y0: KOT.katlar[0] - KOT.doseme, y1: ust, modul: 1.0, vKes: [...KOT.katlar, KOT.cati], mat: m.koyugri });
    }
  }

  // 2) Otopark katı kaidesi — antrasit kompozit (±0.00 … +2.70)
  const kH = KOT.katlar[0] - KOT.doseme;
  const KS = KAPLAMA.ofs + KAPLAMA.kal; // köşe sarma payı
  for (const [p, q, n, uz] of [
    [[448.4, 1037.5], [1024.1, 1037.5], KUZEY, [KS, 0]], [[1151.4, 1037.5], [1727.2, 1037.5], KUZEY, [0, 0]],
    [[448.4, 1616.0], [1024.1, 1616.0], GUNEY, [KS, 0]], [[1151.4, 1616.0], [1727.2, 1616.0], GUNEY, [0, KS]],
    [[448.4, 1037.5], [448.4, 1616.0], BATI, [0, 0]], [[1727.2, 1230.2], [1727.2, 1616.0], DOGU, [0, 0]],
  ]) kaplama(g, m, { a: Z(...p), b: Z(...q), nDis: n, y0: 0, y1: kH, modul: 1.25, mat: m.antrasit, uzat: uz });

  // 3) Merdiven yarıkları (bina girişi) — ahşap tonlu kompozit lambri, ±0.00 … parapet üstü
  const lambriKot = [...KOT.katlar, KOT.cati];
  const girisKapi = (a, b) => { const L = b.clone().sub(a).length(); return [[L / 2 - 0.6, L / 2 + 0.6, 0, 2.4]]; };
  {
    const a = N(1057.4, 1168.0), b = N(1186.8, 1168.0);
    kaplama(g, m, { a, b, nDis: KUZEY, y0: 0, y1: ust, bosluk: girisKapi(a, b), modul: 0.2, vKes: lambriKot, mat: m.ahsap, lambri: true });
    kaplama(g, m, { a: N(1057.4, 1099.6), b: N(1057.4, 1168.0), nDis: DOGU, y0: 0, y1: ust, modul: 0.2, vKes: lambriKot, mat: m.ahsap, lambri: true, uzat: [KS, 0] });
    kaplama(g, m, { a: N(1186.8, 1099.6), b: N(1186.8, 1168.0), nDis: BATI, y0: 0, y1: ust, modul: 0.2, vKes: lambriKot, mat: m.ahsap, lambri: true, uzat: [KS, 0] });
    // giriş kapısı: antrasit kasa + koyu cam (görünüşteki "BİNA GİRİŞİ")
    const c = N(1122.1, 1168.0), z = c.y - KAPLAMA.ofs * 0.5;
    const kp = (w, h, x, y, dz, mat) => { const b2 = golge(new THREE.Mesh(new THREE.BoxGeometry(w, h, dz), mat)); b2.position.set(x, y, z); g.add(b2); };
    kp(1.2, 2.4, c.x, 1.2, 0.03, m.kapiCam);
    kp(1.2, 0.07, c.x, 2.365, 0.06, m.alu); kp(0.07, 2.33, c.x - 0.565, 1.165, 0.055, m.alu); kp(0.07, 2.33, c.x + 0.565, 1.165, 0.055, m.alu);
    kp(0.03, 1.2, c.x + 0.4, 1.1, 0.12, m.alu);
  }
  kaplama(g, m, { a: N(1057.4, 1561.5), b: N(1186.8, 1561.5), nDis: GUNEY, y0: 0, y1: ust, modul: 0.2, vKes: lambriKot, mat: m.ahsap, lambri: true });
  kaplama(g, m, { a: N(1057.4, 1561.5), b: N(1057.4, 1687.0), nDis: DOGU, y0: 0, y1: ust, modul: 0.2, vKes: lambriKot, mat: m.ahsap, lambri: true, uzat: [0, KS] });
  kaplama(g, m, { a: N(1186.8, 1561.5), b: N(1186.8, 1687.0), nDis: BATI, y0: 0, y1: ust, modul: 0.2, vKes: lambriKot, mat: m.ahsap, lambri: true, uzat: [0, KS] });

  // 4) Balkon cepleri — arka duvar, yan duvar ve tavan ahşap tonlu kompozit; dış kenarlarda cam korkuluk
  const balkonlar = [
    { arka: [[472.8, 1125.6], [702.9, 1125.6], KUZEY], yan: [[702.9, 1047.9], [702.9, 1125.6], BATI], kose: [[472.8, 1047.9], [702.9, 1125.6]], pen: [531.6, 633.3, 1125.6] },
    { arka: [[1541.3, 1125.6], [1771.4, 1125.6], KUZEY], yan: [[1541.3, 1047.9], [1541.3, 1125.6], DOGU], kose: [[1541.3, 1047.9], [1771.4, 1125.6]], pen: [1610.9, 1712.6, 1125.6] },
    { arka: [[472.8, 1661.2], [702.9, 1661.2], GUNEY], yan: [[702.9, 1661.2], [702.9, 1738.9], BATI], kose: [[472.8, 1661.2], [702.9, 1738.9]], pen: [531.6, 633.3, 1661.2] },
    { arka: [[1541.3, 1661.2], [1771.4, 1661.2], GUNEY], yan: [[1541.3, 1661.2], [1541.3, 1738.9], DOGU], kose: [[1541.3, 1661.2], [1771.4, 1738.9]], pen: [1610.9, 1712.6, 1661.2] },
  ];
  for (const bk of balkonlar) {
    const a = N(...bk.arka[0]), b = N(...bk.arka[1]);
    for (const k of KOT.katlar) {
      const tavan = k + KOT.kat - KOT.doseme;
      kaplama(g, m, { a, b, nDis: bk.arka[2], y0: k, y1: tavan, bosluk: pencereBoslugu(a, b, bk.pen[0], bk.pen[1], bk.pen[2], [k]), modul: 0.2, mat: m.ahsap, lambri: true });
      kaplama(g, m, { a: N(...bk.yan[0]), b: N(...bk.yan[1]), nDis: bk.yan[2], y0: k, y1: tavan, modul: 0.2, mat: m.ahsap, lambri: true });
      tavanLambri(g, m, N(...bk.kose[0]), N(...bk.kose[1]), tavan, m.ahsap);
    }
  }
  for (const kenar of BALKON_KENARLARI) {
    const q = kenar.map(p => N(...p));
    const mx = (q[0].x + q[2].x) / 2, mz = (q[0].y + q[2].y) / 2;
    for (let i = 0; i < 2; i++) {
      const a = q[i], b = q[i + 1], mid = new THREE.Vector2().addVectors(a, b).multiplyScalar(0.5);
      const nIc = new THREE.Vector2(mx - mid.x, mz - mid.y);
      if (Math.abs(nIc.x) > Math.abs(nIc.y)) nIc.set(Math.sign(nIc.x), 0); else nIc.set(0, Math.sign(nIc.y));
      // köşede iki kol üst üste binmeden birleşir: ilk kol 3,5 cm, ikinci kol 10,5 cm kısalır
      for (const k of KOT.katlar) camKorkuluk(g, m, a, b, nIc, k, KOT.korkuluk, i === 0 ? [0, 0.035] : [0.105, 0]);
    }
  }

  // 5) Dükkan — antrasit kompozit (vitrin boşluğu hariç)
  {
    const { x0, x1, y0, y1 } = DUKKAN, H = KOT.dukkan + KOT.dukkanParapet;
    const a = Z(x0, y0), b = Z(x1, y0);
    const gx = xe => x0 + (VITRIN.batiUcu - xe) * GS / S;
    const u0 = Z(gx(VITRIN.x1), y0).x - a.x, u1 = Z(gx(VITRIN.x0), y0).x - a.x, vH = (VITRIN.zemin - VITRIN.ust) * GS;
    kaplama(g, m, { a, b, nDis: KUZEY, y0: 0, y1: H, bosluk: [[u0, u1, 0, vH]], modul: 1.25, vKes: [vH], mat: m.antrasit, uzat: [KS, KS] });
    kaplama(g, m, { a: Z(x1, y0), b: Z(x1, y1), nDis: DOGU, y0: 0, y1: H, modul: 1.2, vKes: [2.7], mat: m.antrasit });
    kaplama(g, m, { a: Z(1727.2, y1), b: Z(x1, y1), nDis: GUNEY, y0: 0, y1: H, modul: 1.25, vKes: [2.7], mat: m.antrasit, uzat: [0, KS] });
    kaplama(g, m, { a: Z(x0, y0), b: Z(x0, 986.4), nDis: BATI, y0: 0, y1: H, modul: 1.0, vKes: [2.7], mat: m.antrasit });
    kaplama(g, m, { a: Z(x0, 986.4), b: Z(x0, 1037.5), nDis: BATI, y0: 0, y1: kH, modul: 1.0, mat: m.antrasit });
    const p = [Z(x0, y0), Z(x1, y0), Z(x1, y1), Z(x0, y1)];
    g.add(halka(disOfset(p, 0.06), 0.28, H, H + 0.03, m.alu)); // harpuşta
  }

  // 6) Konut çatı parapeti harpuştası (antrasit metal)
  g.add(halka(disOfset(NORMAL_DIS.map(p => N(...p)), 0.06), 0.28, ust, ust + 0.03, m.alu));

  // 7) Pencere arkasında oda hacmi (camdan bakınca bina içi boş görünmesin)
  for (const [x0, x1, y] of PENCERELER) {
    const c = N((x0 + x1) / 2, y), kuzey = y < 1393.4;
    const nIc = kuzey ? GUNEY : KUZEY;
    for (const k of KOT.katlar) {
      const h = KOT.kat - KOT.doseme, D = 3.0, W = 2.5;
      const arka = golge(new THREE.Mesh(new THREE.BoxGeometry(W, h, 0.05), m.icDuvar), false, true);
      arka.position.set(c.x, k + h / 2, c.y + nIc.y * D); g.add(arka);
      for (const sx of [-1, 1]) {
        const yan = golge(new THREE.Mesh(new THREE.BoxGeometry(0.05, h, D - 0.25), m.icDuvar), false, true);
        yan.position.set(c.x + sx * W / 2, k + h / 2, c.y + nIc.y * (0.25 + (D - 0.25) / 2)); g.add(yan);
      }
    }
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

function arsa(m, uzunYol = false) {
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
  if (!uzunYol) {
    const yol = [
      new THREE.Vector2(x0, z0), new THREE.Vector2(x1, z0), new THREE.Vector2(x1, z1), Fg,
      F, E, pr[3], pr[2], pr[1], pr[0], new THREE.Vector2(x0, pr[0].y),
    ];
    g.add(golge(yukselt(yol, 0, 0.012, m.asfalt), false, true));
  } else {
    // Fotogerçekçi görünüşler için yollar boyuna uzatılır; genişlik (maket payı) temsilidir
    const U = 400, kG = pr[0].y - z0;            // 706. Sokak: parsel sınırından kuzeye
    const nE = new THREE.Vector2(-dir.y, dir.x); if (nE.x < 0) nE.negate();
    const dG = Fg.clone().sub(F).length();
    const cG = 13;                                // Odunluk Caddesi şeridi (temsili)
    const kuzey = [new THREE.Vector2(-U, pr[0].y - kG), new THREE.Vector2(U, pr[0].y - kG), new THREE.Vector2(U, pr[0].y), pr[1], pr[0], new THREE.Vector2(-U, pr[0].y)];
    const Eu = E.clone().addScaledVector(dir, -U), Fu = F.clone().addScaledVector(dir, U);
    const dogu = [Eu, Fu, Fu.clone().addScaledVector(nE, cG), Eu.clone().addScaledVector(nE, cG)];
    // köşe: parsel köşe eğrisi ile iki şerit arasını doldur
    const kose = [pr[1], pr[2], pr[3], E, E.clone().addScaledVector(nE, cG), new THREE.Vector2(E.x + cG + 30, pr[0].y - kG), new THREE.Vector2(pr[1].x, pr[0].y - kG)];
    [[kuzey, 0.012], [dogu, 0.0125], [kose, 0.013]].forEach(([q, h]) => g.add(golge(yukselt(q, 0, h, m.asfalt), false, true)));
    void dG;
  }

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
  const cw = 0.1, cizilen = new Set();
  for (const yer of OTOPARK_YERLERI) {
    const q = yer.map(p => Z(...p));
    for (let i = 0; i < 4; i++) {
      const a = q[i], b = q[(i + 1) % 4];
      // komşu park yerlerinin ortak kenarı bir kez çizilir (üst üste iki kutu olmasın)
      const anahtar = [a, b].map(v => `${v.x.toFixed(1)},${v.y.toFixed(1)}`).sort().join('|');
      if (cizilen.has(anahtar)) continue;
      cizilen.add(anahtar);
      const d = new THREE.Vector2().subVectors(b, a); const L = d.length(); d.normalize();
      const bx = golge(new THREE.Mesh(new THREE.BoxGeometry(L + cw, 0.01, cw), m.cizgi), false, true);
      bx.position.set((a.x + b.x) / 2, 0.026 + (cizilen.size % 2) * 0.0015, (a.y + b.y) / 2); bx.rotation.y = -Math.atan2(d.y, d.x);
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
  kok.add(arsa(m, mod === 'tasarim'));
  kok.add(konutBlogu(m, mod));
  kok.add(dukkanBlogu(m));
  if (mod === 'tasarim') kok.add(cephe(m));
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
