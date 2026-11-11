"""Özgün arka plan müziği + ses efektleri sentezleyicisi.

Hiçbir hazır sample kullanılmaz: tüm sesler numpy/scipy ile sıfırdan üretilir,
bu yüzden telif riski yoktur. Zamanlama src/timeline.json'dan okunur, böylece
efektler video ile kare hassasiyetinde senkron kalır.

Kullanım: python3 scripts/audio.py src/timeline.json public/soundtrack_raw.wav
"""
import json
import sys
import wave

import numpy as np
from scipy import signal

SR = 48000
rng = np.random.default_rng(7)

tl = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
FPS = tl["fps"]
DUR = tl["durationInFrames"] / FPS
N = int(DUR * SR)

BPM = 120
BEAT = 60 / BPM
DROP = 3.0  # müzik "drop"u = ürün sahnesine geçiş


# ---------------------------------------------------------------- yardımcılar
def t_arr(dur):
    return np.arange(int(dur * SR)) / SR


def env_exp(dur, decay):
    t = t_arr(dur)
    return np.exp(-t / decay)


def adsr(n, a=0.005, r=0.05):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr and nr < n:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def lp(x, fc, order=2):
    b, a = signal.butter(order, min(fc, SR / 2 - 100) / (SR / 2), "low")
    return signal.lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], "band")
    return signal.lfilter(b, a, x)


def sweep_filter(x, f0, f1, q=4.0, block=256):
    """Zamanla frekansı değişen state-variable band-pass (whoosh/riser için)."""
    y = np.zeros_like(x)
    low = band = 0.0
    n = len(x)
    for s in range(0, n, block):
        frac = s / max(n - 1, 1)
        fc = f0 * (f1 / f0) ** frac
        f = 2 * np.sin(np.pi * fc / SR)
        damp = 1 / q
        for i in range(s, min(s + block, n)):
            high = x[i] - low - damp * band
            band += f * high
            low += f * band
            y[i] = band
    return y


def saw(freq, t):
    return 2 * ((t * freq) % 1.0) - 1


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def place(buf, x, at, gain=1.0, pan=0.0):
    """Mono sesi stereo tampona yerleştirir (eşit güç pan)."""
    i = int(at * SR)
    if i >= buf.shape[1]:
        return
    x = x[: buf.shape[1] - i]
    l = np.cos((pan + 1) * np.pi / 4)
    r = np.sin((pan + 1) * np.pi / 4)
    buf[0, i : i + len(x)] += x * gain * l
    buf[1, i : i + len(x)] += x * gain * r


def reverb(st, seconds=1.4, wet=0.18, predelay=0.012):
    out = np.zeros_like(st)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-t / (seconds / 5.5))
        ir = lp(ir, 6000)
        ir[: int(predelay * SR)] = 0
        ir /= np.sqrt(np.sum(ir**2))
        out[ch] = signal.fftconvolve(st[ch], ir)[: st.shape[1]]
    return st * (1 - wet) + out * wet * 2.2


# ----------------------------------------------------------------- enstrümanlar
def kick():
    t = t_arr(0.45)
    f = 45 + 110 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / 0.16)
    click = hp(rng.standard_normal(len(t)), 2000) * np.exp(-t / 0.004) * 0.25
    return np.tanh((body + click) * 1.6) * 0.9


def clap():
    t = t_arr(0.35)
    nz = bp(rng.standard_normal(len(t)), 900, 5000)
    e = np.zeros(len(t))
    for k, off in enumerate([0, 0.011, 0.022]):
        i = int(off * SR)
        e[i:] += np.exp(-(t[: len(t) - i]) / (0.006 if k < 2 else 0.09))
    return nz * e * 0.55


def hat(open_=False):
    t = t_arr(0.25 if open_ else 0.07)
    nz = hp(rng.standard_normal(len(t)), 7000, 3)
    return nz * np.exp(-t / (0.07 if open_ else 0.018)) * 0.35


def bass_note(freq, dur):
    t = t_arr(dur)
    x = np.sin(2 * np.pi * freq * t) + 0.35 * lp(saw(freq, t), 400)
    return x * adsr(len(t), 0.004, 0.04) * 0.55


def supersaw(freqs, dur, cutoff, decay):
    t = t_arr(dur)
    x = np.zeros(len(t))
    for f in freqs:
        for d in (-0.12, -0.05, 0.0, 0.05, 0.12):
            x += saw(f * 2 ** (d / 12), t + rng.random() / f)
    x /= len(freqs) * 5
    x = lp(x, cutoff, 2)
    return x * np.exp(-t / decay) * adsr(len(t), 0.003, 0.03)


def pad(freqs, dur, cutoff=1400):
    t = t_arr(dur)
    x = np.zeros(len(t))
    for f in freqs:
        for d in (-0.08, 0.08):
            ff = f * 2 ** (d / 12)
            x += 0.6 * saw(ff, t + rng.random()) + 0.4 * np.sin(2 * np.pi * ff * t)
    x = lp(x / (len(freqs) * 2), cutoff, 2)
    return x * adsr(len(t), 0.25, 0.4)


def pluck(freq, dur=0.32):
    t = t_arr(dur)
    x = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * 2 * freq * t) * np.exp(-t / 0.05)
    return x * np.exp(-t / 0.12) * adsr(len(t), 0.002, 0.03) * 0.3


# ------------------------------------------------------------------- efektler
def sfx_impact():
    t = t_arr(1.6)
    f = 38 + 70 * np.exp(-t / 0.08)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.45)
    nz = lp(rng.standard_normal(len(t)), 2500) * np.exp(-t / 0.06) * 0.5
    return np.tanh((boom + nz) * 1.4) * 0.8


def sfx_slam():
    t = t_arr(0.5)
    body = np.sin(2 * np.pi * (70 + 120 * np.exp(-t / 0.02)) * t) * np.exp(-t / 0.09)
    nz = bp(rng.standard_normal(len(t)), 300, 4000) * np.exp(-t / 0.03)
    return np.tanh((body + 0.6 * nz) * 1.5) * 0.7


def sfx_whoosh(dur=0.55):
    nz = rng.standard_normal(int(dur * SR))
    y = sweep_filter(nz, 400, 6000, q=1.6)
    t = t_arr(dur)
    e = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    return y * e * 0.9


def sfx_riser(dur):
    nz = rng.standard_normal(int(dur * SR))
    y = sweep_filter(nz, 300, 7000, q=3.0)
    t = t_arr(dur)
    tone = np.sin(2 * np.pi * np.cumsum(220 * 2 ** (2 * t / dur)) / SR) * 0.25
    e = (t / dur) ** 2
    return (y * 0.8 + tone) * e


def sfx_pop():
    t = t_arr(0.12)
    f = 520 + 700 * np.exp(-t / 0.012)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.035) * 0.6


def sfx_tick():
    t = t_arr(0.02)
    return hp(rng.standard_normal(len(t)), 3000) * np.exp(-t / 0.0025) * 0.6


def sfx_ticks(dur):
    out = np.zeros(int((dur + 0.05) * SR))
    k, at = 0, 0.0
    while at < dur:
        x = sfx_tick()
        i = int(at * SR)
        out[i : i + len(x)] += x
        at += 0.035 + 0.05 * (at / dur) ** 2  # sayaç yavaşlayarak durur
        k += 1
    return out


def sfx_ding(base=1318.5):
    t = t_arr(1.2)
    x = np.zeros(len(t))
    for ratio, amp, dec in ((1, 1, 0.5), (2.01, 0.4, 0.25), (3.0, 0.2, 0.15), (4.2, 0.1, 0.1)):
        x += amp * np.sin(2 * np.pi * base * ratio * t) * np.exp(-t / dec)
    x2 = np.zeros_like(x)
    d = int(0.07 * SR)
    t2 = t[: len(t) - d]
    for ratio, amp, dec in ((1, 1, 0.5), (2.01, 0.35, 0.25)):
        x2[d:] += amp * np.sin(2 * np.pi * base * 1.5 * ratio * t2) * np.exp(-t2 / dec)
    return (x + 0.8 * x2) * 0.22 * adsr(len(t), 0.001, 0.05)


def sfx_shimmer():
    out = np.zeros(int(1.3 * SR))
    for k, m in enumerate([81, 84, 88, 91, 93, 96]):
        x = np.sin(2 * np.pi * midi(m) * t_arr(0.6)) * env_exp(0.6, 0.15) * 0.18
        i = int(k * 0.045 * SR)
        out[i : i + len(x)] += x
    return out


def sfx_alert():
    out = np.zeros(int(0.5 * SR))
    for k, m in enumerate([76, 72]):
        x = np.sin(2 * np.pi * midi(m) * t_arr(0.25)) * env_exp(0.25, 0.07) * 0.4
        i = int(k * 0.11 * SR)
        out[i : i + len(x)] += x
    return out


def sfx_tap():
    t = t_arr(0.08)
    x = np.sin(2 * np.pi * 1800 * t) * np.exp(-t / 0.006) + 0.5 * hp(rng.standard_normal(len(t)), 2000) * np.exp(-t / 0.003)
    return x * 0.7


SFX = {
    "impact": lambda c: sfx_impact(),
    "slam": lambda c: sfx_slam(),
    "whoosh": lambda c: sfx_whoosh(),
    "riser": lambda c: sfx_riser(c.get("dur", 1.0)),
    "pop": lambda c: sfx_pop(),
    "ticks": lambda c: sfx_ticks(c.get("dur", 0.8)),
    "ding": lambda c: sfx_ding(),
    "shimmer": lambda c: sfx_shimmer(),
    "alert": lambda c: sfx_alert(),
    "tap": lambda c: sfx_tap(),
}

# ---------------------------------------------------------------------- müzik
# Akor ilerlemesi (Am - F - C - G), drop'tan itibaren 2 sn'lik ölçüler
CHORDS = [
    (45, [57, 60, 64, 69]),  # Am
    (41, [57, 60, 65, 69]),  # F
    (48, [55, 60, 64, 67]),  # C
    (43, [55, 59, 62, 67]),  # G
]
BAR = 4 * BEAT
END_MUSIC = 29.0

drums = np.zeros((2, N))
bass = np.zeros((2, N))
chords = np.zeros((2, N))
pads = np.zeros((2, N))
arps = np.zeros((2, N))
sidechain = np.ones(N)

K, CL, HC, HO = kick(), clap(), hat(), hat(True)


def section(t):
    if t < DROP:
        return "intro"
    if t < 9:
        return "A"
    if t < 17:
        return "B"
    if t < 23:
        return "C"
    if t < 24:
        return "fill"
    if t < END_MUSIC:
        return "D"
    return "end"


# İntro: filtreli pad + tek kick (vuruş giriş darbesiyle beraber)
place(pads, pad([midi(m) for m in CHORDS[0][1]], DROP + 0.2, 700), 0, 0.5)
place(drums, K, 0.0, 0.8)
# İntro'nun son vuruşunda hat stutter
for k in range(8):
    place(drums, HC, DROP - 1.0 + k * BEAT / 4, 0.25 + 0.05 * k, pan=0.2)

# Ana groove
beat_t = DROP
while beat_t < END_MUSIC - 1e-6:
    sec = section(beat_t)
    b_idx = int(round((beat_t - DROP) / BEAT))
    in_bar = b_idx % 4
    # kick 4/4 (C bölümünde yarı yoğunluk)
    if sec != "C" or in_bar in (0, 2):
        place(drums, K, beat_t, 0.85)
        i = int(beat_t * SR)
        n = int(0.22 * SR)
        sc = 1 - 0.55 * np.exp(-np.arange(n) / (0.07 * SR))
        sidechain[i : i + n] = np.minimum(sidechain[i : i + n], sc)
    # clap 2 ve 4'te
    if sec in ("B", "D", "fill") and in_bar in (1, 3):
        place(drums, CL, beat_t, 0.6, pan=-0.05)
    # offbeat hat
    place(drums, HO if sec in ("B", "D") else HC, beat_t + BEAT / 2, 0.45, pan=0.25)
    if sec in ("B", "D"):
        place(drums, HC, beat_t + BEAT / 4, 0.18, pan=-0.3)
        place(drums, HC, beat_t + 3 * BEAT / 4, 0.18, pan=-0.3)
    if sec == "fill":
        for k in range(4):
            place(drums, CL, beat_t + k * BEAT / 4, 0.18 + 0.1 * k)
    beat_t += BEAT

# Bas + akor stab + pad + arp, ölçü ölçü
bar_t = DROP
bar_i = 0
while bar_t < END_MUSIC - 1e-6:
    root, notes = CHORDS[bar_i % 4]
    sec = section(bar_t)
    freqs = [midi(m) for m in notes]
    # bas: senkoplu sekizlikler
    for step in (0, 0.75, 1.5, 2, 2.75, 3.5):
        tt = bar_t + step * BEAT
        if tt < END_MUSIC:
            place(bass, bass_note(midi(root), 0.22), tt, 0.85)
    # akor stab'ları
    if sec != "C":
        for step in (0, 0.75, 1.5, 2.5, 3.25):
            tt = bar_t + step * BEAT
            if tt < END_MUSIC:
                place(chords, supersaw(freqs, 0.4, 2600 if sec != "A" else 1800, 0.13), tt, 0.5)
    # pad (C bölümünde öne çıkar)
    place(pads, pad(freqs, BAR + 0.3, 1800 if sec == "C" else 1100), bar_t, 0.55 if sec == "C" else 0.28)
    # arp (B bölümü: bilgi yoğun kısım)
    if sec in ("B", "D"):
        seq = [notes[0] + 12, notes[2] + 12, notes[1] + 12, notes[3] + 12]
        for k in range(16):
            tt = bar_t + k * BEAT / 4
            if tt < END_MUSIC:
                place(arps, pluck(midi(seq[k % 4])), tt, 0.5, pan=(-0.4 if k % 2 else 0.4))
    bar_t += BAR
    bar_i += 1

# Final akoru: Am, kuyruklu
place(chords, supersaw([midi(m) for m in [57, 60, 64, 69, 76]], 1.0, 3000, 0.45), END_MUSIC, 0.7)
place(bass, bass_note(midi(33), 0.9) * np.linspace(1, 0, int(0.9 * SR)), END_MUSIC, 0.9)
place(drums, K, END_MUSIC, 0.8)

sc2 = np.vstack([sidechain, sidechain])
music = drums * 0.9 + bass * sc2 * 0.8 + chords * sc2 * 0.55 + pads * sc2 * 0.5 + arps * sc2 * 0.4
music = reverb(music, 1.6, 0.14)
# İntroda müzik biraz geride, drop'ta tam seviye
fade_in = np.clip((np.arange(N) / SR) / DROP, 0, 1) * 0.35 + 0.65
fade_in[int(DROP * SR) :] = 1.0
music *= fade_in
tail = np.ones(N)
k0 = int((DUR - 0.6) * SR)
tail[k0:] = np.linspace(1, 0, N - k0)
music *= tail

# -------------------------------------------------------------------- SFX
fx = np.zeros((2, N))
for cue in tl["sfx"]:
    x = SFX[cue["type"]](cue)
    pan = {"whoosh": -0.15, "pop": 0.1}.get(cue["type"], 0.0)
    place(fx, x, cue["f"] / FPS, cue.get("gain", 0.5), pan)
fx = reverb(fx, 0.9, 0.12)

mix = music * 0.62 + fx * 0.9
mix = hp(mix, 25)
mix = np.tanh(mix * 1.15) / np.tanh(1.15)
mix /= np.max(np.abs(mix)) / 0.89

pcm = (mix.T * 32767).astype(np.int16)
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("wrote", OUT, f"{DUR:.2f}s")
