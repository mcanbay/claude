"""Approximate word-level alignment of the voiceover to the known script.

No ASR needed: we detect pauses in the audio, align them (monotone DP) to
punctuation/word boundaries using a syllable-rate model, then distribute
word timings inside each speech span by syllable count.

usage: python align.py voice.mp3 timings.json
"""
import json
import subprocess
import sys

import numpy as np

from script_data import CHUNKS

SR = 16000
HOP = 0.01
# chunk id -> approx. time (s) the chunk starts after a pause (manual check)
FORCE_START = {"allah": 51.82, "a1": 54.08}
# chunk starts that must not be pinned to a pause
NO_ANCHOR = {"m6", "ayet85"}
VOWELS = set("aeıioöuüâîûAEIİOÖUÜÂÎÛ")


def syllables(word):
    n = sum(1 for c in word if c in VOWELS)
    return max(n, 1)


def load(path):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def pauses(a, thr_db=-36.0, min_len=0.14):
    hop = int(SR * HOP)
    n = len(a) // hop
    fr = a[: n * hop].reshape(n, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    # smooth a bit
    db = np.convolve(db, np.ones(3) / 3, mode="same")
    sil = db < thr_db
    out = []
    i = 0
    while i < n:
        if sil[i]:
            j = i
            while j < n and sil[j]:
                j += 1
            out.append((i * HOP, j * HOP))
            i = j
        else:
            i += 1
    total = n * HOP
    lead = out[0][1] if out and out[0][0] == 0 else 0.0
    trail = out[-1][0] if out and out[-1][1] >= total - 0.02 else total
    inner = [(s, e) for s, e in out if s > 0 and e < total - 0.02 and e - s >= min_len]
    return lead, trail, inner


def main():
    src, dst = sys.argv[1], sys.argv[2]
    a = load(src)
    lead, trail, ps = pauses(a)

    words = []  # (chunk_idx, text)
    for ci, (_, text) in enumerate(CHUNKS):
        for w in text.split():
            words.append((ci, w))
    syl = np.array([syllables(w) for _, w in words], float)
    cum = np.concatenate([[0], np.cumsum(syl)])  # cum[k] = syllables before word k
    nW = len(words)

    # boundary k (1..nW-1) = after word k-1
    def bweight(k):
        w = words[k - 1][1]
        if w.endswith(("...", ".", "?", ":", ";", '."', '?"')):
            return 0.0
        if w.endswith(","):
            return 0.25
        if words[k][0] != words[k - 1][0]:
            return 0.9  # chunk boundary without punctuation
        return 1.6

    speech_total = (trail - lead) - sum(e - s for s, e in ps)
    rate = cum[-1] / speech_total  # syllables / second of speech

    # actual speech-time position of each pause
    pos = []
    acc = 0.0
    prev = lead
    for s, e in ps:
        acc += s - prev
        pos.append(acc)
        prev = e

    P = len(ps)
    INF = 1e18
    # dp[i][k]: best cost having processed pauses[:i], last used boundary < k
    # We do simple O(P * nW^2) restricted by window.
    exp_t = cum / rate
    dp = np.full((P + 1, nW + 1), INF)
    bt = {}
    dp[0][0] = 0.0
    for i in range(P):
        dur = ps[i][1] - ps[i][0]
        for k in range(nW + 1):
            c0 = dp[i][k]
            if c0 >= INF:
                continue
            # skip this pause (treat as intra-phrase gap)
            skip = c0 + 2.5 * dur * 4
            if skip < dp[i + 1][k]:
                dp[i + 1][k] = skip
                bt[(i + 1, k)] = (i, k, None)
            # assign to boundary b > k
            for b in range(max(k + 1, 1), nW):
                diff = abs(exp_t[b] - pos[i])
                if exp_t[b] - pos[i] > 6:
                    break
                if diff > 6:
                    continue
                c = c0 + diff + bweight(b) * (1.0 + 2.0 * dur)
                if c < dp[i + 1][b]:
                    dp[i + 1][b] = c
                    bt[(i + 1, b)] = (i, k, b)
    k = int(np.argmin(dp[P]))
    assign = {}
    i = P
    while i > 0:
        pi, pk, b = bt[(i, k)]
        if b is not None:
            assign[b] = ps[pi]
        i, k = pi, pk

    # manual fixes after checking pause lengths vs. syllable counts
    first_word = {}
    for wi, (ci, _) in enumerate(words):
        first_word.setdefault(CHUNKS[ci][0], wi)
    for cid, t in FORCE_START.items():
        b = first_word[cid]
        p = min(ps, key=lambda q: abs(q[1] - t))
        for bb in [bb for bb, q in assign.items() if q == p]:
            del assign[bb]
        assign[b] = p
    for cid in NO_ANCHOR:
        assign.pop(first_word[cid], None)
    # drop anything that is no longer monotone
    clean, last_t = {}, -1
    for b in sorted(assign):
        if assign[b][0] > last_t:
            clean[b] = assign[b]
            last_t = assign[b][0]
    assign = clean

    # build anchors: boundary -> (end of prev word, start of next word)
    anchors = [(0, lead, lead)]
    for b in sorted(assign):
        s, e = assign[b]
        anchors.append((b, s, e))
    anchors.append((nW, trail, trail))

    start = np.zeros(nW)
    end = np.zeros(nW)
    for (b0, _, t0), (b1, t1, _) in zip(anchors[:-1], anchors[1:]):
        span = t1 - t0
        sy = cum[b1] - cum[b0]
        for w in range(b0, b1):
            start[w] = t0 + span * (cum[w] - cum[b0]) / sy
            end[w] = t0 + span * (cum[w + 1] - cum[b0]) / sy

    out_words = [
        {"i": i, "chunk": CHUNKS[c][0], "text": w, "start": round(float(start[i]), 3),
         "end": round(float(end[i]), 3)}
        for i, (c, w) in enumerate(words)
    ]
    chunks = []
    for ci, (cid, text) in enumerate(CHUNKS):
        ws = [w for w in out_words if w["chunk"] == cid]
        chunks.append({"id": cid, "text": text, "start": ws[0]["start"], "end": ws[-1]["end"],
                       "words": [w["i"] for w in ws]})
    json.dump({"duration": len(a) / SR, "rate": rate, "words": out_words, "chunks": chunks},
              open(dst, "w"), ensure_ascii=False, indent=1)
    print(f"lead={lead:.2f} trail={trail:.2f} pauses={P} assigned={len(assign)} rate={rate:.2f} syl/s")
    for c in chunks:
        print(f"{c['start']:7.2f} {c['end']:7.2f}  {c['text']}")


if __name__ == "__main__":
    main()
