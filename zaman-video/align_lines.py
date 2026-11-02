"""Word timings from the VoxCPM2 reading summary (ozet.json gives exact t0/t1 per spoken line).

Inside each line, pauses in the audio are snapped to punctuation boundaries and the
words in between are spread by syllable count.

usage: python align_lines.py okuma.wav ozet.json timings.json
"""
import json
import sys

import numpy as np

from align import SR, load, syllables
from script_data import CHUNKS, LINE_CHUNKS, SYLLABLES


def inner_pauses(a, t0, t1, thr_db=-36.0, min_len=0.12):
    hop = int(SR * 0.01)
    seg = a[int(t0 * SR): int(t1 * SR)]
    n = len(seg) // hop
    if n == 0:
        return []
    db = 20 * np.log10(np.sqrt((seg[: n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
    db = np.convolve(db, np.ones(3) / 3, mode="same")
    out, i = [], 0
    while i < n:
        if db[i] < thr_db:
            j = i
            while j < n and db[j] < thr_db:
                j += 1
            s, e = t0 + i * 0.01, t0 + j * 0.01
            if e - s >= min_len and s > t0 + 0.05 and e < t1 - 0.05:
                out.append((s, e))
            i = j
        else:
            i += 1
    return out


def speech_bounds(a, t0, t1, thr_db=-40.0):
    """trim leading/trailing silence of a line"""
    hop = int(SR * 0.01)
    seg = a[int(t0 * SR): int(t1 * SR)]
    n = len(seg) // hop
    db = 20 * np.log10(np.sqrt((seg[: n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
    idx = np.where(db > thr_db)[0]
    if len(idx) == 0:
        return t0, t1
    return t0 + idx[0] * 0.01, t0 + (idx[-1] + 1) * 0.01


def main():
    wav, summary, dst = sys.argv[1:4]
    a = load(wav)
    lines = json.load(open(summary, encoding="utf-8"))["satirlar"]
    assert len(lines) == len(LINE_CHUNKS), (len(lines), len(LINE_CHUNKS))
    text = dict(CHUNKS)
    words = []
    for line, cids in zip(lines, LINE_CHUNKS):
        lw = [(cid, w) for cid in cids for w in text[cid].split()]
        syl = np.array([SYLLABLES.get(w, syllables(w)) for _, w in lw], float)
        cum = np.concatenate([[0], np.cumsum(syl)])
        t0, t1 = speech_bounds(a, line["t0"], line["t1"])
        ps = inner_pauses(a, t0, t1)
        speech = (t1 - t0) - sum(e - s for s, e in ps)
        # candidate boundaries: after punctuation or between chunks
        cand = {}
        for k in range(1, len(lw)):
            w = lw[k - 1][1].rstrip('"')
            if w.endswith((".", "?", ":", ";", ",")) or lw[k][0] != lw[k - 1][0]:
                cand[k] = 0 if w.endswith((".", "?", ":", ";", ",")) else 1
        anchors, used, acc, prev = [(0, t0, t0)], 0, 0.0, t0
        for s, e in ps:
            acc += s - prev
            prev = e
            exp_syl = acc / speech * cum[-1]
            best = None
            for k, pen in cand.items():
                if k <= used:
                    continue
                d = abs(cum[k] - exp_syl) + pen * 1.5
                if d < max(3.0, 0.25 * cum[-1]) and (best is None or d < best[0]):
                    best = (d, k)
            if best:
                anchors.append((best[1], s, e))
                used = best[1]
        anchors.append((len(lw), t1, t1))
        st, en = np.zeros(len(lw)), np.zeros(len(lw))
        for (b0, _, s0), (b1, e1, _) in zip(anchors[:-1], anchors[1:]):
            span, sy = e1 - s0, cum[b1] - cum[b0]
            for k in range(b0, b1):
                st[k] = s0 + span * (cum[k] - cum[b0]) / sy
                en[k] = s0 + span * (cum[k + 1] - cum[b0]) / sy
        for k, (cid, w) in enumerate(lw):
            words.append({"i": len(words), "chunk": cid, "text": w, "start": round(float(st[k]), 3), "end": round(float(en[k]), 3)})
    chunks = []
    for cid, t in CHUNKS:
        ws = [w for w in words if w["chunk"] == cid]
        chunks.append({"id": cid, "text": t, "start": ws[0]["start"], "end": ws[-1]["end"], "words": [w["i"] for w in ws]})
    json.dump({"duration": len(a) / SR, "words": words, "chunks": chunks}, open(dst, "w"), ensure_ascii=False, indent=1)
    for c in chunks:
        print(f"{c['start']:7.2f} {c['end']:7.2f}  {c['text']}")


if __name__ == "__main__":
    main()
