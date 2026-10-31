"""Placeholder timings (no audio yet): syllable-rate model with punctuation pauses.
usage: python synth_timings.py out.json"""
import json, sys
from script_data import CHUNKS
from align import syllables

RATE = 6.0
words, t = [], 0.3
for ci, (cid, text) in enumerate(CHUNKS):
    for w in text.split():
        d = syllables(w) / RATE
        words.append({"i": len(words), "chunk": cid, "text": w, "start": round(t, 3), "end": round(t + d, 3)})
        t += d
        if w.rstrip('"').endswith((".", "?", ":")): t += 0.55
        elif w.endswith(","): t += 0.3
        else: t += 0.03
chunks = []
for cid, text in CHUNKS:
    ws = [w for w in words if w["chunk"] == cid]
    chunks.append({"id": cid, "text": text, "start": ws[0]["start"], "end": ws[-1]["end"], "words": [w["i"] for w in ws]})
json.dump({"duration": t + 0.3, "rate": RATE, "words": words, "chunks": chunks}, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
print("duration", round(t, 1))
