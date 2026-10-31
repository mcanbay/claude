// ---------------------------------------------------------------- topic: Allah katında zaman (Hac 47, Secde 5)
const hooks = [];
const H = fn => hooks.push(fn);

function clock(svg, cx, cy, r, color = '#1f3166', rate = 1, t0 = 0) {
  const g = svgEl(svg, 'g', {});
  const face = svgEl(g, 'circle', { cx, cy, r, fill: 'rgba(255,255,255,.55)', stroke: color, 'stroke-width': Math.max(2.5, r / 28), filter: 'url(#rough)' }, 'draw');
  const ticks = svgEl(g, 'g', {});
  for (let i = 0; i < 12; i++) {
    const a = i / 12 * Math.PI * 2, r1 = r * (i % 3 ? .86 : .78), r2 = r * .93;
    svgEl(ticks, 'line', { x1: cx + Math.cos(a) * r1, y1: cy + Math.sin(a) * r1, x2: cx + Math.cos(a) * r2, y2: cy + Math.sin(a) * r2, stroke: color, 'stroke-width': Math.max(1.5, r / 45), 'stroke-linecap': 'round' });
  }
  const mk = (len, w, c) => {
    const l = svgEl(g, 'line', { x1: cx, y1: cy, x2: cx, y2: cy - len, stroke: c, 'stroke-width': w, 'stroke-linecap': 'round' });
    l.style.transformBox = 'view-box'; l.style.transformOrigin = '0 0';
    return l;
  };
  const hr = mk(r * .5, Math.max(3, r / 16), color), mn = mk(r * .78, Math.max(2, r / 24), '#c8372d');
  svgEl(g, 'circle', { cx, cy, r: Math.max(3, r / 18), fill: color });
  H(t => {
    const tt = Math.max(0, t - t0) * rate;
    mn.setAttribute('transform', `rotate(${(tt * 90) % 360} ${cx} ${cy})`);
    hr.setAttribute('transform', `rotate(${(30 + tt * 7.5) % 360} ${cx} ${cy})`);
  });
  return { g, face, ticks };
}

function quranBook(svg, cx, cy) {
  const book = svgEl(svg, 'g', {});
  for (let i = 0; i < 12; i++) {
    const a = i / 12 * Math.PI * 2;
    svgEl(book, 'line', { x1: cx + Math.cos(a) * 100, y1: cy + Math.sin(a) * 100, x2: cx + Math.cos(a) * 122, y2: cy + Math.sin(a) * 122, stroke: '#e8c93c', 'stroke-width': 3, 'stroke-linecap': 'round' });
  }
  svgEl(book, 'circle', { cx, cy, r: 105, fill: 'url(#glow)', opacity: .7 });
  svgEl(book, 'rect', { x: cx - 65, y: cy - 80, width: 130, height: 160, rx: 4, fill: '#2f6e3c', stroke: '#1d4a27', 'stroke-width': 4 });
  svgEl(book, 'ellipse', { cx, cy, rx: 40, ry: 44, fill: 'none', stroke: '#d8b64a', 'stroke-width': 3 });
  const t = svgEl(book, 'text', { x: cx, y: cy + 10, 'text-anchor': 'middle', 'font-family': 'Amiri', 'font-weight': 700, 'font-size': 28, fill: '#e2c25a' });
  t.textContent = 'القرآن';
  return book;
}

function build() {
  const rings = $('#rings');
  for (let i = 0; i < 15; i++) {
    const cx = 38 + i * 47.5;
    svgEl(rings, 'path', { d: `M${cx - 11},${22} A12,12 0 1,1 ${cx + 11},${22}`, fill: 'none', stroke: '#6f6f72', 'stroke-width': 3.2, 'stroke-linecap': 'round' });
    svgEl(rings, 'circle', { cx: cx + 0.5, cy: 29, r: 5.2, fill: '#2b2b2e' });
  }

  // ---------- S1: clocks / relativity
  const s1 = $('#s1svg');
  const big = clock(s1, 360, 372, 100, '#1f3166', 1, 0);
  const q = svgEl(s1, 'text', { x: 490, y: 330, 'font-family': 'Caveat', 'font-weight': 700, 'font-size': 64, fill: '#c8372d' });
  q.textContent = '?';
  const cL = clock(s1, 215, 562, 58, '#2f9bb3', .3, 0);
  const cR = clock(s1, 505, 562, 58, '#1f3166', 1, 0);
  const slowTag = svgEl(s1, 'text', { x: 215, y: 490, 'text-anchor': 'middle', 'font-family': 'Caveat', 'font-weight': 700, 'font-size': 26, fill: '#2f9bb3' });
  slowTag.textContent = 'yavaş akar';
  const normTag = svgEl(s1, 'text', { x: 505, y: 490, 'text-anchor': 'middle', 'font-family': 'Caveat', 'font-weight': 700, 'font-size': 26, fill: '#1f3166' });
  normTag.textContent = 'daha hızlı akar';

  A('#s1title', 'type', 0, .7);
  A(big.face, 'draw', .1, .7); A(big.ticks, 'fade', .4, .4);
  A('#s1sub', 'wipe', S('sence'), .8);
  A(q, 'pop', S('herkes') + .4, .45); A(q, 'wobble', S('herkes') + .9, 99);
  A('#s1sticky', 'pop', S('einstein'), .45);
  A([big.g, q], 'out', S('hiz') - .2, .4);
  A(cL.g, 'pop', S('hiz'), .45); A('#ck1l', 'fade', S('hiz') + .2, .4);
  A(cR.g, 'pop', S('hiz') + .25, .45); A('#ck2l', 'fade', S('hiz') + .4, .4);
  A('#r1', 'wipe', S('hiz') + .2, .8);
  A('#r2', 'wipe', S('kutle'), .9);
  A(slowTag, 'fade', S('yavas'), .4); A(normTag, 'fade', S('yavas') + .2, .4);
  A('#s1sticky', 'out', S('hiz') - .2, .3);

  // ---------- S2: GPS
  const s2 = $('#s2svg');
  const EX = 220, EY = 520;
  const orbit = svgEl(s2, 'path', { d: `M${EX - 170},${EY} A170,170 0 0,1 ${EX + 170},${EY}`, fill: 'none', stroke: '#9aa0aa', 'stroke-width': 2.5, 'stroke-dasharray': '8 8' });
  const earth = svgEl(s2, 'g', { filter: 'url(#rough)' });
  svgEl(earth, 'circle', { cx: EX, cy: EY, r: 92, fill: '#bfe0ee', stroke: '#2f6f9b', 'stroke-width': 3 });
  svgEl(earth, 'path', { d: `M${EX - 60},${EY - 40} q20,-25 50,-10 q15,20 -5,35 q-25,15 -35,0 z`, fill: '#8cc98a', stroke: '#3f8a4c', 'stroke-width': 2 });
  svgEl(earth, 'path', { d: `M${EX + 10},${EY + 10} q35,-20 55,5 q5,30 -25,45 q-30,0 -30,-50 z`, fill: '#8cc98a', stroke: '#3f8a4c', 'stroke-width': 2 });
  const satOuter = svgEl(s2, 'g', {});
  const sat = svgEl(satOuter, 'g', {});
  svgEl(sat, 'rect', { x: -14, y: -11, width: 28, height: 22, rx: 3, fill: '#e8e3d0', stroke: '#26324f', 'stroke-width': 2.5 });
  svgEl(sat, 'rect', { x: -46, y: -8, width: 28, height: 16, fill: '#5b7fc0', stroke: '#26324f', 'stroke-width': 2 });
  svgEl(sat, 'rect', { x: 18, y: -8, width: 28, height: 16, fill: '#5b7fc0', stroke: '#26324f', 'stroke-width': 2 });
  svgEl(sat, 'line', { x1: 0, y1: 11, x2: 0, y2: 20, stroke: '#26324f', 'stroke-width': 2 });
  const s2t0 = S('teori');
  H(t => {
    const a = (-150 + Math.max(0, t - s2t0) * 4) * Math.PI / 180;
    sat.setAttribute('transform', `translate(${EX + Math.cos(a) * 170},${EY + Math.sin(a) * 170}) rotate(${a * 180 / Math.PI + 90})`);
  });
  const satClock = clock(s2, 580, 330, 44, '#1f3166', 1.15, 0);
  const grClock = clock(s2, 580, 520, 44, '#1f3166', 1, 0);
  // relocate labels
  Object.assign($('#satl').style, { left: '520px', top: '252px' });
  Object.assign($('#plus').style, { left: '470px', top: '378px' });
  Object.assign($('#grl').style, { left: '515px', top: '568px' });
  Object.assign($('#s2sticky').style, { left: '398px', top: '428px', fontSize: '15px' });
  const link = svgEl(s2, 'path', { d: `M${EX + 120},${EY - 120} Q450,300 530,330`, fill: 'none', stroke: '#c8372d', 'stroke-width': 2.2, 'stroke-dasharray': '5 6' });
  // pin drifting
  const trail = svgEl(s2, 'path', { d: 'M110,690 L410,690', fill: 'none', stroke: '#c8372d', 'stroke-width': 3, 'stroke-dasharray': '9 8', 'stroke-linecap': 'round' }, 'draw');
  const pinO = svgEl(s2, 'g', {});
  const pin = svgEl(pinO, 'g', {});
  svgEl(pin, 'path', { d: 'M0,0 C-14,-16 -16,-26 -16,-32 A16,16 0 1,1 16,-32 C16,-26 14,-16 0,0 Z', fill: '#c8372d', stroke: '#8f231c', 'stroke-width': 2 });
  svgEl(pin, 'circle', { cx: 0, cy: -32, r: 6, fill: '#fbe9e7' });
  const realPin = svgEl(s2, 'circle', { cx: 110, cy: 690, r: 7, fill: '#2e8b57' });
  H(t => {
    const p = easeInOut(clamp((t - S('km')) / 2.0));
    pin.setAttribute('transform', `translate(${110 + 300 * p},688)`);
  });
  Object.assign($('#pinl').style, { left: '96px', top: '710px' });

  A('#s2title', 'type', s2t0, .7);
  A(orbit, 'fade', s2t0 + .2, .4);
  A(earth, 'pop', s2t0 + .1, .5);
  A(satOuter, 'pop', S('gps'), .45);
  A(satClock.g, 'pop', S('gps') + .5, .45); A('#satl', 'fade', S('gps') + .6, .4);
  A(grClock.g, 'pop', S('yerdeki'), .45); A('#grl', 'fade', S('yerdeki') + .2, .4);
  A(link, 'fade', S('gps') + .7, .4);
  A('#plus', 'pop', S('mikro'), .5); A('#plus', 'pulse', S('mikro') + .5, 99, { amp: .05 });
  A('#s2sticky', 'pop', S('mikro') + .9, .45);
  A(realPin, 'pop', S('konum'), .35); A(pinO, 'pop', S('konum') + .1, .4);
  A(trail, 'draw', S('km'), 2.0);
  A('#pinl', 'wipe', S('km') + .3, 1.0);
  A('#s2stamp', 'stamp', S('nerede') + .2, .35);

  // ---------- S3: Hac 47
  const s3 = $('#s3svg');
  const book3 = quranBook(s3, 360, 380);
  const num3 = circleNum(s3, 92, 140, 22, '22');
  const s3t = S('kuran');
  A('#s3a', 'type', s3t, .8);
  A(book3, 'pop', S('nediyor'), .55);
  A('#s3a', 'out', S('hac') - .1, .3);
  A(book3, 'out', S('h1') - .45, .35);
  A(num3[0], 'draw', S('hac'), .5); A(num3[1], 'fade', S('hac') + .2, .3);
  A('#s3hdr', 'wipe', S('hac') + .1, .8);
  A('#s3sticky', 'pop', S('ayet47') + .2, .45);
  const hT = [W('h1', 0), W('h1', 2), W('h2', 0), W('h2', 1), W('h3', 0), W('h3', 1), W('h4', 0), W('h4', 1)];
  document.querySelectorAll('#s3 .ar .w').forEach(w => A(w, 'wipeR', hT[+w.dataset.k], .45));
  A('#ht1', 'wipe', S('hm1'), 1.3);
  A('#ht2', 'wipe', S('hm2'), .9);
  A('#ht3', 'wipe', S('hm3'), .8);
  // 1 gün vs 1000 yıl
  const dayBox = svgEl(s3, 'rect', { x: 186, y: 642, width: 14, height: 14, rx: 2, fill: '#1f3166' });
  const yrBar = svgEl(s3, 'rect', { x: 96, y: 690, width: 528, height: 14, rx: 4, fill: 'rgba(200,55,45,.75)' });
  const yrTicks = svgEl(s3, 'g', {});
  for (let i = 1; i < 10; i++) svgEl(yrTicks, 'line', { x1: 96 + i * 52.8, y1: 686, x2: 96 + i * 52.8, y2: 708, stroke: '#efede5', 'stroke-width': 2 });
  A('#tl1', 'fade', S('hm3') - .4, .4); A(dayBox, 'pop', S('hm3') - .3, .35);
  A(yrBar, 'grow', S('hm3') + .1, 1.2); A(yrTicks, 'fade', S('hm3') + 1.1, .3);
  A('#tl2', 'fade', S('hm3') + .8, .5);

  // ---------- S4: Secde 5 + Meâric 4
  const s4 = $('#s4svg');
  const num4 = circleNum(s4, 92, 140, 22, '32');
  const s4t = S('secde');
  A(num4[0], 'draw', s4t, .5); A(num4[1], 'fade', s4t + .2, .3);
  A('#s4hdr', 'wipe', s4t + .1, .8);
  A('#s4sticky', 'pop', S('isler') + .2, .45);
  const sT = [W('s1', 0), W('s1', 1), W('s1', 2), W('s2', 0), W('s3', 0), W('s3', 1), W('s4', 0), W('s4', 1)];
  document.querySelectorAll('#s4 .ar .w').forEach(w => A(w, 'wipeR', sT[+w.dataset.k], .45));
  A('#st1', 'wipe', S('sm1'), 1.6);
  A('#st2', 'wipe', S('sm3') + .2, .6);
  // comparison bars
  const bars = [[598, 10], [658, 10], [718, 524]].map(([y, w], i) =>
    svgEl(s4, 'rect', { x: 96, y, width: w, height: 14, rx: 3, fill: i === 2 ? 'rgba(200,55,45,.8)' : '#1f3166' }));
  Object.assign($('#b1v').style, { left: '116px', top: '586px' });
  Object.assign($('#b2v').style, { left: '116px', top: '646px' });
  Object.assign($('#b3v').style, { left: '440px', top: '738px' });
  A('#b1l', 'wipe', S('mearic'), .5); A(bars[0], 'pop', S('mearic') + .3, .3); A('#b1v', 'fade', S('mearic') + .4, .3);
  A('#b2l', 'wipe', S('mearic') + .5, .5); A(bars[1], 'pop', S('mearic') + .8, .3); A('#b2v', 'fade', S('mearic') + .9, .3);
  A('#b3l', 'wipe', S('melek'), 1.0);
  A(bars[2], 'grow', S('elli') - .1, 1.4);
  A('#b3v', 'pop', S('elli') + 1.0, .45);

  // ---------- S5: mimmâ teuddûn
  const s5 = $('#s5svg');
  const s5t = S('dikkat');
  const ul = svgEl(s5, 'path', { d: 'M222,166 q140,10 276,-2', fill: 'none', stroke: '#c8372d', 'stroke-width': 3.5, 'stroke-linecap': 'round', filter: 'url(#rough)' }, 'draw');
  const dcs = [[170, 330, 26, 1], [360, 330, 40, .4], [550, 330, 56, .12]].map(([x, y, r, rate]) => clock(s5, x, y, r, '#1f3166', rate, 0));
  A('#s5title', 'type', s5t, .7); A(ul, 'draw', s5t + .5, .4);
  A('#d1', 'wipe', S('tek'), 1.4);
  dcs.forEach((c, i) => { A(c.g, 'pop', S('bahsetmiyor') + i * .3, .45); A('#dc' + (i + 1), 'fade', S('bahsetmiyor') + i * .3 + .2, .35); });
  A('#mm', 'wipeR', S('vurgu') + .3, .8);
  A('#mml', 'wipe', S('saydiginiz'), .9);
  A('#d2', 'wipe', S('saatimiz'), 1.2);
  A('#s5stamp', 'stamp', S('olcu') + .3, .35);

  // ---------- S6: sonuç
  const s6 = $('#s6svg');
  const hg = svgEl(s6, 'g', {});
  const HX = 160, HY = 420;
  const glass = svgEl(hg, 'path', { d: `M${HX - 52},${HY - 110} L${HX + 52},${HY - 110} C${HX + 52},${HY - 40} ${HX + 8},${HY - 20} ${HX + 8},${HY} C${HX + 8},${HY + 20} ${HX + 52},${HY + 40} ${HX + 52},${HY + 110} L${HX - 52},${HY + 110} C${HX - 52},${HY + 40} ${HX - 8},${HY + 20} ${HX - 8},${HY} C${HX - 8},${HY - 20} ${HX - 52},${HY - 40} ${HX - 52},${HY - 110} Z`, fill: 'rgba(255,255,255,.45)', stroke: '#26324f', 'stroke-width': 3, filter: 'url(#rough)' }, 'draw');
  const capT = svgEl(hg, 'rect', { x: HX - 66, y: HY - 122, width: 132, height: 12, rx: 3, fill: '#8a5a3b' });
  const capB = svgEl(hg, 'rect', { x: HX - 66, y: HY + 110, width: 132, height: 12, rx: 3, fill: '#8a5a3b' });
  const sandTop = svgEl(hg, 'path', { d: `M${HX - 40},${HY - 70} L${HX + 40},${HY - 70} C${HX + 30},${HY - 35} ${HX + 6},${HY - 20} ${HX},${HY - 4} C${HX - 6},${HY - 20} ${HX - 30},${HY - 35} ${HX - 40},${HY - 70} Z`, fill: '#e3b45a' });
  const sandBot = svgEl(hg, 'path', { d: `M${HX - 48},${HY + 106} L${HX + 48},${HY + 106} C${HX + 30},${HY + 70} ${HX + 10},${HY + 50} ${HX},${HY + 46} C${HX - 10},${HY + 50} ${HX - 30},${HY + 70} ${HX - 48},${HY + 106} Z`, fill: '#e3b45a' });
  const stream = svgEl(hg, 'line', { x1: HX, y1: HY - 4, x2: HX, y2: HY + 104, stroke: '#e3b45a', 'stroke-width': 2.5, 'stroke-dasharray': '4 5' });
  sandTop.style.transformBox = 'fill-box'; sandTop.style.transformOrigin = '50% 100%';
  sandBot.style.transformBox = 'fill-box'; sandBot.style.transformOrigin = '50% 100%';
  const s6t = S('yaratan');
  H(t => {
    const p = clamp((t - (s6t + 1)) / (TM.duration - s6t + .5));
    sandTop.style.transform = `scale(${1 - .85 * p},${1 - .85 * p})`;
    sandBot.style.transform = `scale(${.35 + .65 * p},${.35 + .65 * p})`;
    stream.style.strokeDashoffset = -t * 30;
  });
  A('#s6title', 'type', s6t, 1.2);
  A([glass, capT, capB], 'draw', S('icinde'), .8);
  A([sandTop, sandBot, stream], 'fade', S('icinde') + .6, .4);
  A('#s6sticky', 'pop', S('anlatir'), .45);
  A('#q1', 'wipe', S('nekadar'), .9); A('#q1b', 'wipe', S('nekadar') + .9, .4);
  A('#q2', 'wipe', S('birgun2'), 1.8);
  A('#z6', 'wipe', S('pekisen'), 2.6);

  // ---------- scene windows
  const sc = [['#s1', 0, S('teori')], ['#s2', S('teori'), S('kuran')], ['#s3', S('kuran'), S('secde')],
    ['#s4', S('secde'), S('dikkat')], ['#s5', S('dikkat'), S('yaratan')], ['#s6', S('yaratan'), 1e9]];
  sc.forEach(([id, a, b]) => { A(id, 'show', a - .25, .25, { end: b - .25 }); });
}

// after fonts/layout: highlight boxes + circles positioned from real text boxes
function layoutDynamic() {
  const stage = $('#stage').getBoundingClientRect();
  const box = el => { const r = el.getBoundingClientRect(); return { x: r.left - stage.left, y: r.top - stage.top, w: r.width, h: r.height }; };
  const hl = (sel, id, t, dur) => {
    const el = $(sel), b = box(el), parent = el.closest('.scene');
    const pb = box(parent);
    const d = document.createElement('div');
    d.className = 'hl'; d.id = id;
    Object.assign(d.style, { left: (b.x - pb.x - 4) + 'px', top: (b.y - pb.y + b.h * .42) + 'px', width: (b.w + 8) + 'px', height: (b.h * .5) + 'px', zIndex: 0 });
    parent.insertBefore(d, parent.firstChild.nextSibling);
    A('#' + id, 'wipe', t, dur);
  };
  hl('#mk1', 'hl1', S('hm1') + .6, .6);
  hl('#mk2', 'hl2', S('hm2') + .3, .6);
  hl('#mk3', 'hl3', S('sm3'), .4);

  const circ = (scene, ks, labelSel, t, where) => {
    const svg = $(scene + 'svg');
    const words = [...document.querySelectorAll(scene + ' .ar .w')];
    const bs = ks.map(k => box(words[k]));
    const x0 = Math.min(...bs.map(b => b.x)), x1 = Math.max(...bs.map(b => b.x + b.w));
    const y0 = Math.min(...bs.map(b => b.y)), y1 = Math.max(...bs.map(b => b.y + b.h));
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2 + 4, rx = (x1 - x0) / 2 + 10, ry = (y1 - y0) / 2 - 4;
    const e = svgEl(svg, 'ellipse', { cx, cy, rx, ry, fill: 'none', stroke: '#c8372d', 'stroke-width': 3, filter: 'url(#rough)' }, 'draw');
    const lab = $(labelSel);
    lab.style.left = '0px';
    const lr = lab.getBoundingClientRect();
    if (where === 'left') { lab.style.top = (cy - lr.height / 2) + 'px'; lab.style.left = (cx - rx - 10 - lr.width) + 'px'; }
    else if (where === 'above') { lab.style.top = (cy - ry - lr.height + 4) + 'px'; lab.style.left = (cx - lr.width / 2) + 'px'; }
    else { lab.style.top = (cy + ry - 6) + 'px'; lab.style.left = (cx - lr.width / 2) + 'px'; }
    A(e, 'draw', t, .45);
    A(labelSel, 'fade', t + .25, .35);
  };
  circ('#s3', [2, 3], '#hc2', S('hm1') + .1, 'left');
  circ('#s3', [1], '#hc1', S('hm1') + 1.0, 'above');
  circ('#s3', [6, 7], '#hc4', S('hm2') + .1, 'left');
  circ('#s3', [4, 5], '#hc3', S('hm3'), 'below');
  circ('#s4', [3], '#sc1', S('sm1'), 'left');
  circ('#s4', [4, 5], '#sc2', S('sm3'), 'below');
  // big mimmâ teuddûn circle
  const mb = box($('#mmw'));
  const me = svgEl($('#s5svg'), 'ellipse', { cx: mb.x + mb.w / 2, cy: mb.y + mb.h / 2 + 6, rx: mb.w / 2 + 22, ry: mb.h / 2, fill: 'none', stroke: '#c8372d', 'stroke-width': 3.5, filter: 'url(#rough)' }, 'draw');
  A(me, 'draw', S('mimma'), .5);

  ['#s2stamp', '#s5stamp'].forEach(s => { const el = $(s); el.style.left = (360 - el.getBoundingClientRect().width / 2) + 'px'; });
}
