"""
Ses izi: tamamen sentezlenmiş (telifsiz) müzik ve efektler + isteğe bağlı
seslendirme kayıtları.

Müzik sahnelerle eşleşir: mutfakta neşeli marimba, hayal dünyasında
büyülü pad ve arpej, kalkışta davul, brokoli karşısında dramatik vuruşlar,
kapanışta müzik kutusu. Seslendirme dosyası bulunursa müzik ve efektler
konuşma süresince kısılır (ducking).
"""

import subprocess
import wave
from pathlib import Path

import numpy as np

SR = 44100
_rng = np.random.default_rng(7)
AUDIO_EXT = (".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac", ".opus")


# ------------------------------------------------------------------ temel --

def _t(dur):
    return np.arange(int(dur * SR)) / SR


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def m(name):
    """'A4' -> MIDI numarası."""
    n, o = name[:-1], int(name[-1])
    return 12 * (o + 1) + NOTE[n]


def attack(x, a=0.004, r=0.01):
    n = len(x)
    env = np.ones(n)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    env[:na] = np.linspace(0, 1, na)
    env[-nr:] *= np.linspace(1, 0, nr)
    return x * env


def fft_filter(x, lo=None, hi=None):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if lo:
        g *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi:
        g *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * g, len(x))


def noise(dur):
    return _rng.standard_normal(int(dur * SR))


# ----------------------------------------------------------------- çalgılar --

def marimba(f, dur=0.6):
    t = _t(dur)
    x = (np.sin(2 * np.pi * f * t) * np.exp(-t * 6) + 0.35 * np.sin(2 * np.pi * 3.93 * f * t) * np.exp(-t * 16)
         + 0.1 * np.sin(2 * np.pi * 9.2 * f * t) * np.exp(-t * 40))
    return attack(x, 0.002)


def pluck(f, dur=0.5, bright=0.6):
    t = _t(dur)
    x = np.zeros_like(t)
    for k in range(1, 7):
        x += np.sin(2 * np.pi * k * f * t) / k ** 1.3 * np.exp(-t * (3 + k * k * bright))
    return attack(x * 0.6, 0.003)


def musicbox(f, dur=1.4):
    t = _t(dur)
    x = (np.sin(2 * np.pi * f * t) * np.exp(-t * 2.4) + 0.35 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 4.5)
         + 0.18 * np.sin(2 * np.pi * 5.4 * f * t) * np.exp(-t * 10))
    return attack(x, 0.002, 0.05)


def pad(freqs, dur, att=0.6, rel=0.8, bright=3000):
    t = _t(dur)
    x = np.zeros_like(t)
    for f in freqs:
        for det in (-0.004, 0.0, 0.0045):
            ff = f * (1 + det)
            vib = 1 + 0.002 * np.sin(2 * np.pi * 5 * t + f)
            ph = 2 * np.pi * ff * np.cumsum(vib) / SR
            x += np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)
    x /= max(1, len(freqs) * 3)
    env = np.minimum(1, t / att) * np.minimum(1, (dur - t) / rel)
    return fft_filter(x * np.clip(env, 0, 1), hi=bright)


def brass(f, dur, bright=1400):
    t = _t(dur)
    x = np.zeros_like(t)
    for k in range(1, 12):
        x += np.sin(2 * np.pi * k * f * t) / k
    env = np.minimum(1, t / 0.03) * np.exp(-t * 1.2)
    env *= np.minimum(1, (dur - t) / 0.15).clip(0, 1)
    return fft_filter(x * env * 0.4, hi=bright)


def bass(f, dur=0.3):
    t = _t(dur)
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)
    return attack(np.tanh(1.5 * x) * np.exp(-t * 4), 0.004, 0.03)


def kick():
    t = _t(0.35)
    f = 45 + 110 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def hat(dur=0.06):
    x = np.diff(noise(dur + 1 / SR))
    return x * np.exp(-_t(dur) * 70) * 0.35


def clap():
    x = fft_filter(noise(0.2), lo=900, hi=5000)
    t = _t(0.2)
    return x * np.exp(-t * 22) * 0.6


def timpani(f=hz(m("A1")), dur=1.5):
    t = _t(dur)
    x = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 1.5 * f * t) * np.exp(-t * 3)
    x += 0.3 * fft_filter(noise(dur), hi=400) * np.exp(-t * 20)
    return x * np.exp(-t * 2.5)


# ---------------------------------------------------------------- efektler --

def whoosh(dur=0.6, f0=300, f1=3000, gain=1.0):
    n = int(dur * SR)
    x = noise(dur)
    out = np.zeros(n)
    hop = 1024
    win = np.hanning(2 * hop)
    for i in range(0, n - 2 * hop, hop):
        u = i / max(1, n - 2 * hop)
        fc = f0 * (f1 / f0) ** u
        seg = fft_filter(x[i:i + 2 * hop], lo=fc * 0.6, hi=fc * 1.6)
        out[i:i + 2 * hop] += seg * win
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
    return out * env * gain


def sweep(f0, f1, dur, harm=1, gain=1.0):
    t = _t(dur)
    f = f0 * (f1 / f0) ** (t / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = sum(np.sin(k * ph) / k for k in range(1, harm + 1))
    return attack(x * gain, 0.01, 0.05)


def rumble(dur):
    x = fft_filter(noise(dur), hi=160) * 3 + 0.4 * np.sin(2 * np.pi * 42 * _t(dur))
    return x


def beep(f, dur=0.12):
    t = _t(dur)
    x = np.sign(np.sin(2 * np.pi * f * t)) * 0.25 + np.sin(2 * np.pi * f * t) * 0.5
    return attack(fft_filter(x, hi=5000), 0.003, 0.02)


def ping(f=1320, dur=1.2):
    t = _t(dur)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 4)
    echo = np.zeros_like(x)
    d = int(0.18 * SR)
    echo[d:] = x[:-d] * 0.4
    return x + echo


def slide_whistle(f0, f1, dur):
    t = _t(dur)
    f = f0 + (f1 - f0) * (t / dur) ** 0.8
    f = f * (1 + 0.02 * np.sin(2 * np.pi * 7 * t))
    return attack(np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.6, 0.01, 0.04)


def scratch(dur=0.25):
    t = _t(dur)
    f = 900 * (1 - t / dur) + 200
    x = fft_filter(noise(dur), lo=300, hi=3000) * 0.5 + np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4
    return x * np.exp(-t * 6)


def pop():
    t = _t(0.16)
    f = 900 * np.exp(-t * 25) + 180
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 26) + 0.2 * noise(0.16) * np.exp(-t * 120)


def plop():
    t = _t(0.18)
    f = 380 * np.exp(-t * 18) + 110
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 18)


def tick(high=True):
    t = _t(0.06)
    f = 1900 if high else 1400
    return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 2.7 * f * t)) * np.exp(-t * 90) * 0.5


def chirp_cricket(dur, f=4600, period=0.9, offset=0.0):
    t = _t(dur)
    out = np.zeros_like(t)
    car = np.sin(2 * np.pi * f * t)
    for start in np.arange(offset, dur, period):
        for k in range(3):
            s0 = start + k * 0.045
            mask = (t >= s0) & (t < s0 + 0.03)
            out[mask] += np.sin(np.pi * (t[mask] - s0) / 0.03)
    return car * out * 0.25


def shimmer(dur=0.9, base=m("A5"), up=True):
    out = np.zeros(int((dur + 1.2) * SR))
    scale = [0, 3, 5, 7, 10, 12, 15, 17, 19, 22, 24]
    n = len(scale)
    for i, step in enumerate(scale):
        s = int(i / n * dur * SR)
        note = musicbox(hz(base + (step if up else scale[-1] - step)), 1.0) * 0.35
        out[s:s + len(note)] += note
    return out


# ---------------------------------------------------------------- miksaj --

class Bus:
    def __init__(self, dur):
        self.x = np.zeros((int(dur * SR) + SR, 2))

    def add(self, sig, at, gain=1.0, pan=0.0):
        s = int(at * SR)
        if s >= len(self.x) or len(sig) == 0:
            return
        sig = sig[: len(self.x) - s]
        l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
        if sig.ndim == 1:
            self.x[s:s + len(sig), 0] += sig * gain * l * 1.414
            self.x[s:s + len(sig), 1] += sig * gain * r * 1.414
        else:
            self.x[s:s + len(sig)] += sig * gain

    def seq(self, start, bpm, notes, instr, gain=1.0, pan=0.0, until=None):
        """notes: [(vuruş, nota, süre_vuruş), ...]; nota: 'C5' ya da MIDI ya da [nota, ...]"""
        beat = 60.0 / bpm
        for b, n, L in notes:
            at = start + b * beat
            if until is not None and at >= until:
                continue
            ns = n if isinstance(n, (list, tuple)) else [n]
            for nn in ns:
                mm = m(nn) if isinstance(nn, str) else nn
                self.add(instr(hz(mm), max(0.12, L * beat * 1.6)), at, gain / len(ns) ** 0.5, pan)


def _fade(x, t0, t1, sr=SR):
    a, b = int(t0 * sr), int(t1 * sr)
    if b > a:
        x[a:b] *= np.linspace(1, 0, b - a)[:, None]
    x[b:] = 0


# ----------------------------------------------------------------- müzik --

def _mutfak_temasi(bus, start, until, gain):
    bpm = 112
    mel = [(0, "E5", .5), (.5, "G5", .5), (1, "C6", 1), (2, "G5", .5), (2.5, "E5", .5), (3, "F5", 1),
           (4, "A5", .5), (4.5, "G5", .5), (5, "F5", .5), (5.5, "E5", .5), (6, "D5", 1), (7, "G4", 1),
           (8, "E5", .5), (8.5, "G5", .5), (9, "C6", 1), (10, "D6", .5), (10.5, "C6", .5), (11, "B5", 1),
           (12, "A5", .5), (12.5, "G5", .5), (13, "E5", .5), (13.5, "D5", .5), (14, "C5", 2)]
    chords = [(0, ["C4", "E4", "G4"]), (4, ["F4", "A4", "C5"]), (6, ["G4", "B4", "D5"]),
              (8, ["C4", "E4", "G4"]), (10, ["F4", "A4", "C5"]), (12, ["G4", "B4", "D5"]), (14, ["C4", "E4", "G4"])]
    bus.seq(start, bpm, mel, marimba, 0.55 * gain, pan=0.15, until=until)
    strum = []
    for b0, ch in chords:
        for k in (0, 1, 1.5):
            strum.append((b0 + k, ch, 0.4))
    bus.seq(start, bpm, strum, lambda f, d: pluck(f, d, 0.9), 0.32 * gain, pan=-0.2, until=until)
    bl = [(b0, ch[0][:-1] + "2", 1) for b0, ch in chords] + [(b0 + 2, ch[0][:-1] + "2", 1) for b0, ch in chords]
    bus.seq(start, bpm, bl, bass, 0.35 * gain, until=until)


def muzik_ve_efekt(dur):
    mus, sfx = Bus(dur), Bus(dur)

    # 1. sahne: mutfak (0-3)
    _mutfak_temasi(mus, 0.0, 3.05, 1.0)
    sfx.add(whoosh(0.9, 200, 900), 0.05, 0.25)
    sfx.add(plop(), 1.27, 0.7)

    # 2. sahne: dönüşüm (3-8)
    sfx.add(shimmer(0.8, m("A5")), 2.95, 0.9)
    sfx.add(whoosh(0.8, 400, 6000), 2.95, 0.35)
    sfx.add(sweep(160, 1300, 0.9, harm=3, gain=0.12), 3.7)
    for k, at in enumerate((4.35, 4.5, 4.65, 4.8)):
        sfx.add(beep(1400 + k * 260, 0.06), at, 0.18, pan=(-0.6 if k % 2 else 0.6))
    mus.add(pad([hz(m(n)) for n in ("A3", "C4", "E4", "B4")], 2.9, 0.8, 0.9), 3.2, 0.5)
    mus.add(pad([hz(m(n)) for n in ("F3", "A3", "C4", "E4")], 2.6, 0.7, 0.6), 5.5, 0.5)
    arp = []
    pat = ["A4", "C5", "E5", "B5", "E5", "C5"]
    for i in range(int((7.0 - 3.6) / (60 / 96 / 2))):
        arp.append((i * 0.5, pat[i % len(pat)] if i < 6 else ["F4", "A4", "C5", "E5", "C5", "A4"][i % 6], 0.5))
    mus.seq(3.6, 96, arp, lambda f, d: musicbox(f, 0.8), 0.22, pan=0.3, until=7.0)
    mus.add(timpani(hz(m("A1")), 1.0) * np.linspace(0.2, 1, int(1.0 * SR)), 6.2, 0.25)
    mus.add(sweep(220, 880, 0.8, harm=4, gain=0.08), 6.4)
    hit = sum(brass(hz(m(n)), 1.0, 2500) for n in ("C3", "G3", "C4", "E4"))
    mus.add(hit, 7.15, 0.35)
    sfx.add(fft_filter(noise(1.2), lo=3000) * np.exp(-_t(1.2) * 3) * 0.25, 7.15, 0.6)

    # 3. sahne: kalkış (8-13)
    sfx.add(sweep(300, 900, 0.45, harm=2, gain=0.1), 8.05, pan=0.3)
    sfx.add(beep(1800, 0.05), 8.55, 0.2)
    sfx.add(fft_filter(noise(1.0), hi=900) * np.exp(-_t(1.0) * 2.5), 8.6, 0.55)
    r = rumble(2.9)
    env = np.minimum(1, _t(2.9) / 0.3) * np.minimum(1, (2.9 - _t(2.9)) / 0.6)
    sfx.add(r * env, 8.6, 0.35)
    sfx.add(whoosh(1.2, 600, 120), 10.6, 0.3)
    bpm, b = 120, 0.5
    for i in range(int((11.3 - 8.6) / b)):
        at = 8.6 + i * b
        mus.add(kick(), at, 0.55)
        mus.add(hat(), at + b / 2, 0.5, pan=0.4)
        if i % 2 == 1:
            mus.add(clap(), at, 0.35)
    bl = []
    for i in range(int((11.3 - 8.6) / (b / 2))):
        bl.append((i * 0.5, "A1" if (i // 4) % 2 == 0 else "F1", 0.5))
    mus.seq(8.6, bpm, bl, bass, 0.4, until=11.3)
    arp2 = ["A4", "C5", "E5", "A5", "G5", "E5", "C5", "E5"]
    mus.seq(8.6, bpm, [(i * 0.25, arp2[i % 8], 0.25) for i in range(int(2.7 / 0.125))],
            lambda f, d: pluck(f, 0.25, 0.4), 0.2, pan=-0.3, until=11.3)
    mus.add(pad([hz(m(n)) for n in ("A3", "E4", "A4")], 2.8, 0.2, 0.5), 8.6, 0.3)
    sfx.add(ping(1320, 1.2), 11.3, 0.35)
    for i in range(7):
        sfx.add(beep(880 if i % 2 == 0 else 660, 0.16), 11.62 + i * 0.2, 0.22)
    mus.add(pad([hz(m(n)) for n in ("A2", "D#3", "A3")], 1.6, 0.1, 0.4, bright=1200), 11.6, 0.35)

    # 4. sahne: karşılaşma (13-17.4)
    for at, notes, L in ((13.05, ("D2", "D3"), 0.45), (13.6, ("D#2", "D#3"), 0.45), (14.2, ("B1", "F#2", "B2"), 2.2)):
        mus.add(sum(brass(hz(m(n)), L, 900) for n in notes), at, 0.5)
        mus.add(timpani(hz(m(notes[0])), 1.2), at, 0.45)
    t = _t(3.9)
    drone = (np.sin(2 * np.pi * hz(m("A1")) * t) + 0.5 * np.sin(2 * np.pi * hz(m("E2")) * t)) \
        * (0.7 + 0.3 * np.sin(2 * np.pi * 0.7 * t))
    drone *= np.minimum(1, t / 0.6) * np.minimum(1, (3.9 - t) / 0.2)
    mus.add(drone, 13.5, 0.25)
    glass = np.sin(2 * np.pi * hz(m("E6")) * t * (1 + 0.004 * np.sin(2 * np.pi * 5 * t)))
    mus.add(glass * np.minimum(1, t / 1.5) * np.minimum(1, (3.9 - t) / 0.3), 13.5, 0.05, pan=0.5)
    for i in range(6):
        sfx.add(tick(i % 2 == 0), 16.62 + i * 0.13, 0.5)
    sfx.add(scratch(), 17.36, 0.4)
    sfx.add(slide_whistle(1300, 380, 0.4), 17.42, 0.3)
    pizz = [(0, "C4", .5), (1, "E4", .5), (2, "G4", .5), (2.5, "F#4", .5), (3, "F4", .5), (4, "E4", .5),
            (5, "C4", .5), (6, "D4", .5), (6.5, "D#4", .5), (7, "E4", 1)]
    mus.seq(17.75, 140, pizz, lambda f, d: pluck(f, 0.22, 1.4), 0.55, pan=0.2, until=19.95)
    mus.seq(17.75, 140, [(0, "C2", 1), (2, "G1", 1), (4, "C2", 1), (6, "G1", 1)], bass, 0.3, until=19.95)

    # 5. sahne: gerçek dünya (20-26)
    sfx.add(pop(), 20.3, 0.7)
    sfx.add(whoosh(0.4, 3000, 300), 20.0, 0.25)
    _mutfak_temasi(mus, 20.45, 22.95, 0.8)
    sfx.add(sweep(500, 760, 0.6, gain=0.05), 21.0, pan=0.6)
    sfx.add(sweep(760, 520, 0.6, gain=0.05), 21.8, pan=0.6)
    sfx.add(chirp_cricket(2.9, 4600, 0.9, 0.1) + chirp_cricket(2.9, 5200, 1.1, 0.55), 23.15, 0.9, pan=0.3)

    # kapanış (26-30)
    sfx.add(whoosh(0.8, 300, 2500), 25.9, 0.2)
    lull = [(0, "E5", 1), (1, "G5", 1), (2, "C6", 1.5), (3.5, "B5", .5), (4, "A5", 1), (5, "G5", 1),
            (6, "E5", 1), (7, "D5", 1), (8, "C5", 3)]
    mus.seq(26.15, 92, lull, musicbox, 0.5, pan=0.1, until=29.6)
    mus.add(pad([hz(m(n)) for n in ("C3", "G3", "E4")], 2.2, 0.5, 0.6), 26.1, 0.35)
    mus.add(pad([hz(m(n)) for n in ("F3", "A3", "C4", "E4")], 1.8, 0.5, 1.2), 28.2, 0.35)
    sfx.add(shimmer(0.7, m("C6")), 27.2, 0.55)
    sfx.add(shimmer(0.6, m("G5")), 28.9, 0.4)
    return mus, sfx


# ------------------------------------------------------------- seslendirme --

def _oku(path):
    """Ses dosyasını ffmpeg ile 44.1 kHz stereo float'a çevirir."""
    cmd = ["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]
    data = subprocess.run(cmd, capture_output=True, check=True).stdout
    x = np.frombuffer(data, np.float32).reshape(-1, 2).astype(np.float64)
    # baştaki/sondaki sessizliği kırp
    a = np.abs(x).max(axis=1)
    idx = np.where(a > 0.01)[0]
    if len(idx):
        x = x[max(0, idx[0] - int(0.02 * SR)): idx[-1] + int(0.05 * SR)]
    peak = np.abs(x).max() or 1.0
    return x / peak * 0.9


def bul(klasor, ad):
    if not klasor.is_dir():
        return None
    for ext in AUDIO_EXT:
        p = klasor / (ad + ext)
        if p.exists():
            return p
    return None


def ses_izi(path, dur, replikler, klasor, muzik=True):
    """Müzik + efekt + seslendirme karışımını WAV olarak yazar; bulunan replikleri döndürür."""
    n = int(dur * SR)
    if muzik:
        mus, sfx = muzik_ve_efekt(dur)
        mus_x, sfx_x = mus.x[:n], sfx.x[:n]
    else:
        mus_x = sfx_x = np.zeros((n, 2))
    voice = Bus(dur)
    duck = np.zeros(n)
    bulunan = []
    for ad, t0, t1, _, _ in replikler:
        p = bul(Path(klasor), ad)
        if p is None:
            continue
        x = _oku(p)
        voice.add(x, t0, 1.0)
        s, e = int(t0 * SR), min(n, int(t0 * SR) + len(x))
        duck[s:e] = 1.0
        bulunan.append(p.name)
    if bulunan:
        k = int(0.12 * SR)
        duck = np.convolve(duck, np.ones(k) / k, mode="same")
    g = (1 - 0.6 * duck)[:, None]
    mix = mus_x * 0.9 * g + sfx_x * (1 - 0.35 * duck)[:, None] + voice.x[:n] * 1.0
    fade = int(0.6 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
    peak = np.abs(mix).max() or 1.0
    mix = np.tanh(mix / peak * 1.2) / np.tanh(1.2) * 0.89
    pcm = (mix * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return bulunan
