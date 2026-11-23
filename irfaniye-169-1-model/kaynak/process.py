import json, sys

S = 30.8  # pt per meter on unit-plan pages (stair tread = 0.30 m)
src = json.load(open(sys.argv[1]))
out = {}


def r2(v):
    return round(v, 3)


def edge_gaps(walls, bbox, side, tol=0.6):
    """Find uncovered intervals along an exterior edge of the bbox."""
    x0, y0, x1, y1 = bbox
    iv = []
    for w in walls:
        a, b, c, d = w
        if side == 'N' and b <= y0 + tol:
            iv.append((a, c))
        if side == 'S' and d >= y1 - tol:
            iv.append((a, c))
        if side == 'W' and a <= x0 + tol:
            iv.append((b, d))
        if side == 'E' and c >= x1 - tol:
            iv.append((b, d))
    lo, hi = (x0, x1) if side in 'NS' else (y0, y1)
    iv.sort()
    gaps = []
    cur = lo
    for a, b in iv:
        if a > cur + 0.5:
            gaps.append((cur, a))
        cur = max(cur, b)
    if hi > cur + 0.5:
        gaps.append((cur, hi))
    return gaps


for key, v in src.items():
    L = v['left_bbox']
    ox, oy = L[0], L[1]
    tm = lambda x, y: (r2((x - ox) / S), r2((y - oy) / S))
    unit = {}
    for side_name, bb, walls in (('L', v['left_bbox'], v['walls_left']), ('R', v['right_bbox'], v['walls_right'])):
        ws = [[*tm(w[0], w[1]), *tm(w[2], w[3])] for w in walls]
        gaps = []
        for side in 'NSEW':
            for a, b in edge_gaps(walls, bb, side):
                if side in 'NS':
                    y = bb[1] if side == 'N' else bb[3]
                    p0, p1 = tm(a, y), tm(b, y)
                else:
                    x = bb[0] if side == 'W' else bb[2]
                    p0, p1 = tm(x, a), tm(x, b)
                gaps.append({'side': side, 'a': p0, 'b': p1})
        unit[side_name] = {'bbox': [*tm(bb[0], bb[1]), *tm(bb[2], bb[3])], 'walls': ws, 'gaps': gaps}
    floors = []
    for kind, polys in (('dark', v['floor_dark']), ('light', v['floor_light'])):
        for p in polys:
            if len(p) < 3:
                continue
            pts = [tm(x, y) for x, y in p]
            floors.append({'k': kind, 'p': pts})
    labels = []
    lab = v['labels']
    # pair names with area strings below them
    names = [l for l in lab if 'm²' not in l[0]]
    areas = [l for l in lab if 'm²' in l[0]]
    for n in names:
        best = min(areas, key=lambda a: abs(a[1] - n[1]) + abs(a[2] - n[2] - 6.6))
        x, y = tm(n[1], n[2] + 3)
        labels.append([n[0], best[0], x, y])
    core = []
    for s in v['core_strokes']:
        if s[0] == 're':
            core.append(['re', *tm(s[1], s[2]), *tm(s[3], s[4]), r2(s[5])])
        else:
            core.append(['l', *tm(s[0], s[1]), *tm(s[2], s[3]), r2(s[4])])
    out[key] = {'units': unit, 'floors': floors, 'labels': labels, 'core': core}

json.dump(out, open(sys.argv[2], 'w'), separators=(',', ':'), ensure_ascii=False)
for k, v in out.items():
    print(k)
    for s in 'LR':
        u = v['units'][s]
        print(' ', s, u['bbox'])
        for g in u['gaps']:
            print('    gap', g)
    print('  labels', v['labels'])
    print('  floors', len(v['floors']), [ (f['k'], len(f['p'])) for f in v['floors']][:50])
