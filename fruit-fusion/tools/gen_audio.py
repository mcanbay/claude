#!/usr/bin/env python3
"""Synthesises all Fruit Fusion sound effects and the music loop (original, generated in code).
Usage: python3 tools/gen_audio.py   (needs numpy and ffmpeg)"""
import os, subprocess, wave
import numpy as np

SR = 44100
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "audio")


def t(d): return np.arange(int(SR * d)) / SR
def env(n, a=0.005, r=0.05):
    e = np.ones(n); na, nr = max(int(SR * a), 1), max(int(SR * r), 1)
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e
def norm(x, peak=0.7): return x / max(np.max(np.abs(x)), 1e-9) * peak
def save(name, x, peak=0.7):
    x = norm(x, peak)
    with wave.open(os.path.join(OUT, name), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())
def sweep(d, f0, f1, curve=1.0):
    x = t(d); f = f0 + (f1 - f0) * (x / d) ** curve
    return np.sin(2 * np.pi * np.cumsum(f) / SR)
def bell(freq, d, decay=6.0, harm=(1, 0.35, 0.12)):
    x = t(d); s = sum(a * np.sin(2 * np.pi * freq * (i + 1) * x) for i, a in enumerate(harm))
    return s * np.exp(-decay * x) * env(len(x), 0.003, 0.02)
def place(buf, snd, at):
    i = int(at * SR); n = min(len(snd), len(buf) - i)
    if n > 0: buf[i:i + n] += snd[:n]


def sfx():
    d = 0.16; x = t(d)
    save("sfx_drop.wav", sweep(d, 420, 150, 0.6) * np.exp(-22 * x) * env(len(x)), 0.6)
    d = 0.26; x = t(d)
    pop = sweep(d, 380, 920, 0.5) * np.exp(-14 * x) + 0.4 * sweep(d, 760, 1840, 0.5) * np.exp(-20 * x)
    save("sfx_merge.wav", pop * env(len(x), 0.004, 0.04))
    buf = np.zeros(int(SR * 0.95))
    for i, f in enumerate([523.25, 659.25, 783.99, 1046.5, 1318.5, 1568.0]):
        place(buf, bell(f, 0.6, 7.0), i * 0.06)
    save("sfx_fusion.wav", buf * env(len(buf), 0.002, 0.1))
    d = 0.06; x = t(d)
    save("sfx_click.wav", np.sin(2 * np.pi * 1200 * x) * np.exp(-70 * x) * env(len(x), 0.001, 0.01), 0.5)
    buf = np.zeros(int(SR * 0.42))
    place(buf, bell(660, 0.2, 12, (1, 0.2)), 0.0); place(buf, bell(554.37, 0.22, 12, (1, 0.2)), 0.18)
    save("sfx_warning.wav", buf, 0.6)
    buf = np.zeros(int(SR * 1.25))
    for i, f in enumerate([523.25, 440.0, 349.23, 261.63]):
        place(buf, bell(f, 0.6, 5.0, (1, 0.3, 0.1)), i * 0.2)
    save("sfx_gameover.wav", buf * env(len(buf), 0.002, 0.15))
    buf = np.zeros(int(SR * 1.05))
    for i, f in enumerate([523.25, 659.25, 783.99, 1046.5, 783.99, 1046.5, 1318.5]):
        place(buf, bell(f, 0.45, 7.0), i * 0.085)
    save("sfx_newbest.wav", buf * env(len(buf), 0.002, 0.12))


def note(m): return 440.0 * 2 ** ((m - 69) / 12)


def music():
    bpm = 96; beat = 60 / bpm; bars = 16; total = bars * 4 * beat  # 40 s
    n = int(SR * total); buf = np.zeros(n + SR * 2)
    # C  Am  F  G | C  Em  F  G   (twice), original melody over pentatonic.
    chords = [(48, [60, 64, 67]), (45, [57, 60, 64]), (41, [57, 60, 65]), (43, [59, 62, 67]),
              (48, [60, 64, 67]), (40, [59, 64, 67]), (41, [57, 60, 65]), (43, [59, 62, 67])] * 2
    mel = [[76, 0, 79, 76, 72, 0, 74, 0], [72, 0, 69, 72, 76, 0, 72, 0], [77, 0, 76, 72, 69, 0, 72, 0], [74, 0, 71, 74, 79, 0, 74, 0],
           [76, 79, 84, 0, 79, 0, 76, 0], [79, 0, 76, 71, 76, 0, 79, 0], [81, 0, 77, 72, 77, 0, 81, 0], [79, 0, 74, 71, 74, 0, 0, 0]]
    mel = mel + [[m + 0 for m in b] for b in mel]
    rng = np.random.default_rng(1)
    for b, (root, tri) in enumerate(chords):
        t0 = b * 4 * beat
        x = t(4 * beat)
        pad = sum(np.sin(2 * np.pi * note(m) * x) + 0.3 * np.sin(2 * np.pi * note(m) * 2 * x) for m in tri)
        place(buf, 0.10 * pad * env(len(x), 0.25, 0.5), t0)
        for k in (0, 1.5, 2, 3):
            xb = t(beat * 0.9)
            place(buf, 0.42 * np.sin(2 * np.pi * note(root) * xb) * np.exp(-3.5 * xb) * env(len(xb), 0.01, 0.05), t0 + k * beat)
        for k in range(8):  # light arpeggio on off-beats
            if k % 2 == 1:
                place(buf, 0.10 * bell(note(tri[(k // 2) % 3] + 12), 0.3, 12, (1, 0.2)), t0 + k * beat / 2)
            xs = t(0.04)
            place(buf, 0.035 * rng.standard_normal(len(xs)) * np.exp(-90 * xs), t0 + k * beat / 2)
        for k, m in enumerate(mel[b]):
            if m:
                place(buf, 0.30 * bell(note(m), 0.7, 5.5, (1, 0.45, 0.15, 0.05)), t0 + k * beat / 2)
    buf[:len(buf) - n] += buf[n:]  # wrap the tail into the head -> seamless loop
    loop = norm(buf[:n], 0.5)
    tmp = os.path.join(OUT, "_music.wav")
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((loop * 32767).astype("<i2").tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:a", "libvorbis", "-b:a", "96k",
                    os.path.join(OUT, "music_loop.ogg")], check=True)
    os.remove(tmp)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    sfx(); music()
    for f in sorted(os.listdir(OUT)):
        if not f.endswith(".import"): print(f, os.path.getsize(os.path.join(OUT, f)))
