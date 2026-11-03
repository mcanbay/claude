"""Sahne zamanlaması + ses izi.

Seslendirme (VoxCPM2 okuma.wav + ozet.json) varsa her satır sesten kesilir, sahnedeki
yerine konur; ağız senkronu için kare başına genlik zarfı çıkarılır. Ses yoksa satır
süreleri hece sayısından tahmin edilir (sessiz taslak).

Kullanım:
    python3 zamanla.py --taslak
    python3 zamanla.py --ses assets/okuma.mp3 --ozet assets/voice_ozet.json

Çıktı: assets/timings.json (sahne işaretleri, kelime zamanları, ağız zarfı),
       out/ses_mix.wav (ses + efektler; render.js videoya ekler).
"""
import argparse
import json
import subprocess
import wave
from pathlib import Path

import numpy as np

SR = 48000
FPS = 30
ROOT = Path(__file__).resolve().parent

# Seslendirme satırları (seslendirme_satirlar.txt ile aynı sırada)
LINES = [
    {"id": "l1", "kim": "usta", "text": "Herkes buraya bakıyor."},
    {"id": "l2", "kim": "temel", "text": "Ama asıl mesele benim!"},
]
VOWELS = set("aeıioöuüâîûAEIİOÖUÜ")


def syllables(w):
    return max(1, sum(c in VOWELS for c in w))


# ---------------------------------------------------------------- ses yardımcıları
def load_audio(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def save_wav(path, a):
    a = np.clip(a, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((a * 32767).astype("<i2").tobytes())


def db_frames(a, hop):
    n = len(a) // hop
    if n == 0:
        return np.array([-120.0])
    return 20 * np.log10(np.sqrt((a[: n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)


def speech_bounds(a, t0, t1, thr_db=-40.0):
    hop = SR // 100
    seg = a[int(t0 * SR): int(t1 * SR)]
    db = db_frames(seg, hop)
    idx = np.where(db > thr_db)[0]
    if len(idx) == 0:
        return t0, t1
    return t0 + idx[0] * 0.01, t0 + (idx[-1] + 1) * 0.01


def lowpass(x, alpha):
    """Tek kutuplu alçak geçiren; alpha sabit ya da örnek başına dizi."""
    y = np.empty_like(x)
    acc = 0.0
    al = np.broadcast_to(np.asarray(alpha, np.float64), x.shape)
    for i in range(len(x)):
        acc += al[i] * (x[i] - acc)
        y[i] = acc
    return y


def alpha_for(fc):
    return 1 - np.exp(-2 * np.pi * np.asarray(fc, np.float64) / SR)


# ---------------------------------------------------------------- efektler (sentez)
rng = np.random.default_rng(7)


def sfx_whoosh(dur, f_lo=250, f_hi=2600):
    n = int(dur * SR)
    x = np.linspace(0, 1, n)
    noise = rng.standard_normal(n)
    fc = f_lo + (f_hi - f_lo) * np.sin(np.pi * x) ** 1.5
    band = lowpass(noise, alpha_for(fc)) - lowpass(noise, alpha_for(120))
    env = np.sin(np.pi * np.clip(x, 0, 1)) ** 2
    out = band * env
    return out / (np.abs(out).max() + 1e-9)


def sfx_thud(dur=1.2, f0=72, f1=40):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 6)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = (np.sin(ph) + 0.45 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph)) * np.exp(-t * 3.2)
    click = lowpass(rng.standard_normal(n), alpha_for(380)) * np.exp(-t * 28) * 3
    rumble = lowpass(rng.standard_normal(n), alpha_for(90)) * np.exp(-t * 2.2) * 4
    out = body + click + rumble
    out *= np.minimum(1, t / 0.004)
    return out / (np.abs(out).max() + 1e-9)


def sfx_ting(freqs=(2093, 3136, 4186), dur=0.9):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * (5 + i * 2)) / (i + 1) for i, f in enumerate(freqs))
    out *= np.minimum(1, t / 0.003)
    return out / (np.abs(out).max() + 1e-9)


def sfx_pop(dur=0.09, f0=520, f1=980):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 + (f1 - f0) * t / dur
    out = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / dur) ** 2
    return out / (np.abs(out).max() + 1e-9)


def place(track, clip, t, gain):
    i = int(t * SR)
    if i >= len(track):
        return
    j = min(len(track), i + len(clip))
    track[i:j] += clip[: j - i] * gain


# ---------------------------------------------------------------- zamanlama
def schedule(d1, d2):
    """Satır sürelerinden sahne işaretleri."""
    m = {}
    m["l1_0"] = 1.75
    m["l1_1"] = m["l1_0"] + d1
    m["desc0"] = m["l1_1"] + 0.45
    m["desc1"] = m["desc0"] + 2.3
    m["wake"] = m["desc1"] + 0.12
    m["l2_0"] = m["desc1"] + 0.75
    m["l2_1"] = m["l2_0"] + d2
    m["rev0"] = m["l2_1"] + 0.55
    m["rev1"] = m["rev0"] + 1.7
    m["end"] = m["rev1"] + 3.0
    return {k: round(v, 3) for k, v in m.items()}


def word_times(text, s, e, gap=0.04):
    ws = text.split()
    syl = np.array([syllables(w) for w in ws], float)
    cum = np.concatenate([[0], np.cumsum(syl)]) / syl.sum()
    span = e - s
    return [{"text": w, "start": round(s + span * cum[k], 3), "end": round(s + span * cum[k + 1] - gap, 3)}
            for k, w in enumerate(ws)]


def draft_envelope(n_frames, lines):
    env = np.zeros(n_frames)
    for ln in lines:
        for w in ln["words"]:
            k = syllables(w["text"])
            ws, we = w["start"], w["end"]
            for j in range(k):
                a, b = ws + (we - ws) * j / k, ws + (we - ws) * (j + 1) / k
                for f in range(int(a * FPS), int(b * FPS) + 1):
                    if f < n_frames:
                        x = (f / FPS - a) / max(1e-3, b - a)
                        if 0 <= x <= 1:
                            env[f] = max(env[f], np.sin(np.pi * x) * 0.85)
    return env


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ses", help="VoxCPM2 okuma.wav / .mp3")
    ap.add_argument("--ozet", help="VoxCPM2 ozet.json (satır t0/t1)")
    ap.add_argument("--taslak", action="store_true", help="ses olmadan tahmini zamanlama")
    args = ap.parse_args()

    clips = []
    if args.ses and not args.taslak:
        a = load_audio(args.ses)
        ozet = json.load(open(args.ozet, encoding="utf-8"))["satirlar"]
        assert len(ozet) == len(LINES), (len(ozet), len(LINES))
        for row, ln in zip(ozet, LINES):
            t0, t1 = speech_bounds(a, row["t0"], row["t1"])
            t0, t1 = max(0.0, t0 - 0.03), min(len(a) / SR, t1 + 0.08)
            c = a[int(t0 * SR): int(t1 * SR)].copy()
            fade = int(0.012 * SR)
            c[:fade] *= np.linspace(0, 1, fade)
            c[-fade:] *= np.linspace(1, 0, fade)
            clips.append(c)
            print(f"satır {row['satir']}: {t0:.2f}-{t1:.2f} sn  {row['metin']}")
        durs = [len(c) / SR for c in clips]
        mode = "ses"
    else:
        durs = [0.21 * sum(syllables(w) for w in ln["text"].split()) + 0.25 for ln in LINES]
        mode = "taslak"

    m = schedule(*durs)
    n = int(np.ceil(m["end"] * SR))
    voice = np.zeros(n, np.float32)
    lines = []
    for k, ln in enumerate(LINES):
        s = m[f"{ln['id']}_0"]
        if clips:
            place(voice, clips[k], s, 1.0)
            # kelimeler: konuşmanın kesilmiş sınırları içinde heceye göre
            c = clips[k]
            b0, b1 = speech_bounds(c, 0, len(c) / SR, -38)
            words = word_times(ln["text"], s + b0, s + b1)
        else:
            words = word_times(ln["text"], s + 0.05, s + durs[k] - 0.15)
        lines.append({**ln, "start": s, "end": round(s + durs[k], 3), "words": words})

    n_frames = int(np.ceil(m["end"] * FPS))
    if clips:
        peak = np.abs(voice).max()
        voice *= 0.89 / (peak + 1e-9)
        hop = SR // FPS
        db = db_frames(np.concatenate([voice, np.zeros(hop * 2, np.float32)]), hop)[:n_frames]
        env = np.clip((db + 42) / 26, 0, 1)
        env = np.convolve(env, [0.25, 0.5, 0.25], mode="same")
    else:
        env = draft_envelope(n_frames, lines)
    spk = np.zeros(n_frames, int)
    for k, ln in enumerate(lines):
        spk[int(ln["start"] * FPS): int(ln["end"] * FPS) + 1] = k + 1

    # efektler
    sfx = np.zeros(n, np.float32)
    place(sfx, sfx_pop(), m["l1_0"] - 0.05, 0.10)
    place(sfx, sfx_ting(), lines[0]["words"][1]["start"], 0.07)      # "buraya" -> cephe parlar
    place(sfx, sfx_ting((2637, 3951, 5274)), lines[0]["words"][2]["start"] + 0.1, 0.05)
    place(sfx, sfx_whoosh(2.3), m["desc0"], 0.16)
    place(sfx, sfx_thud(), m["wake"], 0.30)
    place(sfx, sfx_pop(0.1, 420, 760), m["l2_0"] - 0.06, 0.10)
    place(sfx, sfx_thud(0.9, 64, 44), lines[1]["words"][3]["start"], 0.22)  # "benim!"
    place(sfx, sfx_whoosh(1.7, 200, 1400), m["rev0"], 0.09)
    place(sfx, sfx_ting((1568, 2349, 3136)), m["rev1"] - 0.1, 0.08)

    mix = voice + sfx
    out_dir = ROOT / "out"
    out_dir.mkdir(exist_ok=True)
    save_wav(out_dir / "ses_mix.wav", mix)
    if clips:
        save_wav(out_dir / "voice_yerlesik.wav", voice)

    data = {"mode": mode, "fps": FPS, "duration": m["end"], "marks": m, "lines": lines,
            "env": [round(float(v), 3) for v in env], "spk": spk.tolist()}
    (ROOT / "assets").mkdir(exist_ok=True)
    json.dump(data, open(ROOT / "assets/timings.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"mod: {mode}  süre: {m['end']:.2f} sn")
    for k, v in m.items():
        print(f"  {k:6s} {v:6.2f}")
    for ln in lines:
        print(f"  {ln['start']:5.2f}-{ln['end']:5.2f} {ln['kim']:6s} " + " ".join(f"{w['text']}@{w['start']:.2f}" for w in ln["words"]))


if __name__ == "__main__":
    main()
