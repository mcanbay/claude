import json, sys
import pymupdf as fitz

PDF = sys.argv[1]
OUT = sys.argv[2]
d = fitz.open(PDF)


def wall_quads(page, bbox_pred):
    out = []
    for g in page.get_drawings():
        r = g['rect']
        if not g['items'] or g['items'][0][0] != 'qu':
            continue
        if not bbox_pred(r):
            continue
        rects = []
        for it in g['items']:
            if it[0] == 'qu':
                q = it[1]
                xs = [q.ul.x, q.ur.x, q.ll.x, q.lr.x]
                ys = [q.ul.y, q.ur.y, q.ll.y, q.lr.y]
                rects.append([min(xs), min(ys), max(xs), max(ys)])
        out.append((r, rects))
    return out


def strokes(page, region):
    x0, y0, x1, y1 = region
    segs = []
    for g in page.get_drawings():
        if g['type'] != 's':
            continue
        r = g['rect']
        if r.x0 < x0 or r.x1 > x1 or r.y0 < y0 or r.y1 > y1:
            continue
        for it in g['items']:
            if it[0] == 'l':
                segs.append([it[1].x, it[1].y, it[2].x, it[2].y, g.get('width') or 0])
            elif it[0] == 're':
                rr = it[1]
                segs.append(['re', rr.x0, rr.y0, rr.x1, rr.y1, g.get('width') or 0])
    return segs


def fills(page, region, op):
    x0, y0, x1, y1 = region
    polys = []
    for g in page.get_drawings():
        if g['type'] not in ('f', 'fs'):
            continue
        r = g['rect']
        if r.x0 < x0 - 1 or r.x1 > x1 + 1 or r.y0 < y0 - 1 or r.y1 > y1 + 1:
            continue
        o = g.get('fill_opacity')
        if o is None or abs(o - op) > 0.01:
            continue
        cur = []
        for it in g['items']:
            if it[0] == 'l':
                a, b = it[1], it[2]
                if cur and (abs(cur[-1][0] - a.x) > 0.05 or abs(cur[-1][1] - a.y) > 0.05):
                    polys.append(cur); cur = []
                if not cur:
                    cur.append((a.x, a.y))
                cur.append((b.x, b.y))
            elif it[0] == 're':
                rr = it[1]
                if cur: polys.append(cur); cur = []
                polys.append([(rr.x0, rr.y0), (rr.x1, rr.y0), (rr.x1, rr.y1), (rr.x0, rr.y1)])
        if cur: polys.append(cur)
    return polys


def labels(page, region):
    x0, y0, x1, y1 = region
    out = []
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            t = ''.join(s['text'] for s in l['spans']).strip()
            bb = l['bbox']
            cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
            if t and x0 <= cx <= x1 and y0 <= cy <= y1:
                out.append([t, cx, cy])
    return out


res = {}
for key, pno in (('u31', 1), ('u21', 2)):
    page = d[pno]
    qs = wall_quads(page, lambda r: r.width > 150)
    qs.sort(key=lambda t: t[0].x0)
    L, R = qs[0], qs[1]
    region = (L[0].x0 - 2, L[0].y0 - 70, R[0].x1 + 2, R[0].y1 + 70)
    res[key] = {
        'left_bbox': [L[0].x0, L[0].y0, L[0].x1, L[0].y1],
        'right_bbox': [R[0].x0, R[0].y0, R[0].x1, R[0].y1],
        'walls_left': L[1], 'walls_right': R[1],
        'core_strokes': strokes(page, (L[0].x1 - 1, region[1], R[0].x0 + 1, region[3])),
        'floor_dark': fills(page, region, 0.247059),
        'floor_light': fills(page, region, 0.098039),
        'labels': labels(page, region),
        'all_strokes': strokes(page, region),
    }

json.dump(res, open(OUT, 'w'))
for k, v in res.items():
    print(k, v['left_bbox'], v['right_bbox'], len(v['walls_left']), len(v['walls_right']),
          len(v['core_strokes']), len(v['floor_dark']), len(v['floor_light']), len(v['labels']))
