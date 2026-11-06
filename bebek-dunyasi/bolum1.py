"""
BEBEĞİN DÜNYASINDA BİR GÜN · BÖLÜM 1
"Mama Sandalyesi mi, Uzay Gemisi mi?" (30 sn, dikey 9:16)

Kullanım:
    python bolum1.py                 # cikti/bolum1_mama_sandalyesi.mp4
    python bolum1.py --preview       # hızlı deneme (540×960, 15 fps)
    python bolum1.py --kare 12.5     # tek kare PNG
    python bolum1.py --kapak         # yalnızca kapak görseli

Seslendirme kayıtları `seslendirme/` klasörüne konursa otomatik eklenir
(dosya adları README'de).
"""

import argparse
import math
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw

from arayuz import (altyazi, dusunce_balonu, hud_uyari, kapanis_karti, konusma_balonu, nisangah)
from cizim import (Bebek, Canvas, S, T, Uzay, W, anne_kol, anne_kol_pov, back_out, bebek_bas, bebek_govde,
                   bebek_kollar, brokoli_gezegen, ease_in, ease_in_out, ease_out, halkali_gezegen,
                   kask_fanus, kask_yaka, keys, kokpit, lerp, mutfak, parilti, rgba, sandalye_arka,
                   sandalye_tepsi, smooth, span, window, WHITE)
import ses

HERE = Path(__file__).resolve().parent
SURE = 30.0

# ------------------------------------------------------------ zaman çizelgesi --
# Sahne sınırları (saniye)
IRIS = (3.0, 3.6)          # mutfak -> uzay (genişleyen daire)
KALKIS = 8.0               # kaşık kumanda koluna dönüşür, motorlar
HEDEF = 11.3               # brokoli gezegeni tespit edilir
KARSILASMA = 13.0          # gezegen yaklaşır
GERI = (20.0, 20.35)       # uzay -> mutfak (sönen baloncuk)
KAPANIS = (26.0, 26.5)     # kapanış kartına geçiş

# Replikler: (dosya adı, başlangıç, bitiş, tür, metin)
# Ses dosyası varsa 'başlangıç' anında çalınır; yazı her durumda ekranda kalır.
REPLIKLER = [
    ("01_anne_yemek_zamani", 0.45, 2.95, "anne", "Haydi bakalım, yemek zamanı!"),
    ("02_bebek_mama_sandalyesi", 3.35, 6.05, "anlatici", "Annem bunun sadece bir mama sandalyesi olduğunu düşünüyor…"),
    ("03_bebek_gorev_basliyor", 6.35, 8.0, "anlatici", "Ama benim için… görev başlıyor."),
    ("04_bebek_yasam_formu", 14.0, 16.9, "anlatici", "Daha önce hiç karşılaşmadığım bir yaşam formu…"),
    ("05_bebek_hazir_degilim", 17.75, 19.95, "bebek", "Bunu araştırmak için henüz hazır değilim."),
    ("06_anne_bir_kasik_daha", 20.55, 23.0, "anne", "Hadi bir kaşık daha…"),
    ("07_bebek_hicbir_sey_bilmiyorsun", 23.4, 26.0, "ic_ses", "Anne… sen hiçbir şey bilmiyorsun."),
]

HEAD = (540.0, 720.0)      # bebeğin başının dünya konumu
TARGET = (850.0, 560.0)    # brokoli gezegeninin ilk göründüğü nokta (ekran)
BLINKS = [2.05, 4.35, 5.5, 9.0, 15.1, 21.4, 24.8]


def _blink(t):
    v = 0.0
    for tb in BLINKS:
        d = abs(t - tb)
        if d < 0.09:
            v = max(v, 1 - d / 0.09)
    return v


def uzayda(t):
    return IRIS[0] <= t < GERI[1]


# -------------------------------------------------------------- bebek pozu --

REST_L, REST_R = (-100.0, 262.0), (100.0, 262.0)


def joystick_lean(t):
    if t < 8.6:
        return 0.0
    return 16 * math.sin(t * 7.0) * window(t, 8.6, 11.4, 0.3, 0.5)


def bebek_poz(t):
    b = Bebek(x=HEAD[0], y=HEAD[1])
    b.blink = _blink(t)
    if t < IRIS[0]:
        # 1. sahne: anne bebeği sandalyeye oturtur, bebek etrafına bakar
        land = 1.25
        b.dy = -330 * (1 - ease_out(span(t, 0.0, land)))
        if land < t < land + 0.3:
            b.dy -= 16 * math.sin(math.pi * span(t, land, land + 0.3))
            b.squash = 0.7 * math.sin(math.pi * span(t, land, land + 0.22))
        held = 1 - smooth(span(t, 1.15, 1.5))
        b.hand_l = (lerp(REST_L[0], -140, held), lerp(REST_L[1], 108, held))
        b.hand_r = (lerp(REST_R[0], 140, held), lerp(REST_R[1], 108, held))
        if t < 1.25:
            b.happy, b.mouth, b.mopen = 1.0, "open", 0.6
        else:
            b.mouth, b.mopen, b.brow = "o", 0.25, 0.6
            b.look = keys(t, [(1.3, (0.0, 0.0)), (1.6, (-1.0, 0.1)), (2.1, (-1.0, 0.1)), (2.35, (1.0, -0.2)),
                              (2.75, (1.0, -0.2)), (3.0, (0.2, -1.0))])
            b.turn = 0.18 * b.look[0]
        return b

    if t < KALKIS:
        # 2. sahne: hayal dünyası, görev başlıyor
        b.helmet = smooth(span(t, 3.5, 4.1))
        if t < 4.6:
            b.mouth, b.mopen, b.brow = "o", 0.7, 1.0
            b.look = keys(t, [(3.0, (0.2, -1.0)), (3.6, (-0.9, -0.6)), (4.15, (0.9, -0.6)), (4.6, (0.0, 0.0))])
        elif t < 6.2:
            b.mouth, b.lid, b.brow_skew = "smirk", 0.3, 0.6
            b.look = keys(t, [(4.6, (0.0, 0.0)), (4.9, (0.95, 0.05))])
            b.turn = keys(t, [(4.6, 0.0), (4.9, 0.12)])
        elif t < 7.1:
            b.mouth, b.brow, b.brow_tilt = "flat", -0.2, keys(t, [(6.2, 0.0), (6.45, 0.85)])
            b.look = keys(t, [(6.2, (0.95, 0.05)), (6.4, (0.0, 0.0))])
        else:
            b.mouth, b.mopen, b.brow_tilt = "grin", 0.75, 0.6
            up = back_out(span(t, 7.1, 7.35))
            b.hand_r = (lerp(REST_R[0], 150, up), lerp(REST_R[1], 40, up))
        return b

    if t < KARSILASMA:
        # 3. sahne: kalkış ve hedef
        b.helmet = 1.0
        lean = joystick_lean(t)
        knob = (150 + lean, 136)
        grab = smooth(span(t, 8.3, 8.6))
        b.hand_r = (lerp(REST_R[0], knob[0], grab), lerp(REST_R[1], knob[1] + 4, grab))
        if t < 8.6:
            b.mouth, b.mopen = "o", 0.4
            b.look = keys(t, [(8.0, (0.0, 0.0)), (8.2, (0.7, 1.0))])
        elif t < 11.3:
            b.mouth, b.mopen = "grin", 0.85
            b.happy = 1.0 if 9.1 < t < 10.4 else 0.0
            wave = window(t, 8.7, 11.1, 0.25, 0.3)
            b.hand_l = (lerp(REST_L[0], -165 + 14 * math.sin(t * 9), wave),
                        lerp(REST_L[1], 55 + 45 * math.sin(t * 13), wave))
            b.dy = -4 * abs(math.sin(t * 13)) * wave
        elif t < 11.6:
            b.mouth, b.mopen = "smile", 0.4
        else:
            b.mouth, b.mopen, b.brow = "o", 0.8, 1.2
            b.look = keys(t, [(11.6, (0.0, 0.0)), (11.75, (0.85, -0.85))])
            b.turn = keys(t, [(11.6, 0.0), (11.8, 0.2)])
            b.dy = -18 * math.sin(math.pi * span(t, 11.6, 11.85))
        return b

    # 4. ve 5. sahne
    b.helmet = 1.0 if t < GERI[0] else 0.0
    if t < GERI[0]:
        knob = (150, 136)
        b.hand_r = (knob[0], knob[1] + 4)
    if t < 16.6:
        b.look, b.turn = (0.9, -0.8), 0.25
        b.mouth, b.mopen, b.brow = "o", 0.45, 0.8
        sus = smooth(span(t, 15.3, 15.7))
        b.lid, b.brow_tilt = 0.34 * sus, 0.55 * sus
        if sus > 0.5:
            b.mouth, b.brow = "flat", 0.2
    elif t < 17.4:
        b.look = keys(t, [(16.6, (0.9, -0.8)), (16.8, (-0.7, -1.0))])
        b.turn = keys(t, [(16.6, 0.25), (16.8, 0.1)])
        b.brow_skew = smooth(span(t, 16.6, 16.8))
        b.mouth = "pursed"
        chin = smooth(span(t, 16.6, 16.85))
        b.hand_l = (lerp(REST_L[0], -26, chin), lerp(REST_L[1], 116, chin))
    elif t < 22.6:
        u = ease_out(span(t, 17.4, 17.7))
        b.turn = lerp(0.1, -0.85, u)
        b.tilt = lerp(0.0, -0.17, u)
        b.lid = 1.0 if u > 0.35 else 0.0
        b.mouth, b.brow = "smirk", 0.3
        down = smooth(span(t, 17.4, 17.7))
        b.hand_l = (lerp(-26, REST_L[0], down), lerp(116, REST_L[1], down))
        if t > 21.0:
            b.dy = -6 * math.sin(math.pi * span(t, 21.0, 21.25))
    else:
        u = ease_in_out(span(t, 22.6, 23.05))
        b.turn = lerp(-0.85, 0.0, u)
        b.tilt = lerp(-0.17, 0.0, u)
        b.lid = 1.0 if u < 0.5 else 0.48
        b.mouth, b.brow = "flat", -0.15
        b.look = (0.0, 0.05)
    if t >= GERI[0]:
        b.hand_r = REST_R
    return b


# ---------------------------------------------------------------- kamera --

def kamera(t):
    """Dünya -> ekran dönüşümü (bebeğin başı çapa noktası)."""
    if t < IRIS[1]:
        z = lerp(1.0, 1.04, smooth(span(t, 0.0, IRIS[1])))
        sx, sy = HEAD
    elif t < KALKIS:
        z = lerp(1.0, 1.07, smooth(span(t, 4.6, 8.0)))
        sx, sy = HEAD
    elif t < KARSILASMA:
        z = lerp(1.07, 1.0, smooth(span(t, 8.0, 8.6)))
        sx, sy = HEAD
    elif t < GERI[0]:
        u = ease_in_out(span(t, 13.0, 14.3))
        z = lerp(1.0, 0.7, u) + 0.04 * smooth(span(t, 14.3, 17.4))
        sx, sy = lerp(HEAD[0], 340, u), lerp(HEAD[1], 1170, u)
    else:
        u = ease_in_out(span(t, 23.0, 25.6))
        z = lerp(1.0, 1.5, u)
        sx, sy = HEAD[0], lerp(HEAD[1], 900, u)
    sh = sarsinti(t)
    return T(sx + sh[0], sy + sh[1]) @ S(z) @ T(-HEAD[0], -HEAD[1])


def sarsinti(t):
    a = keys(t, [(8.6, 0.0), (8.9, 10.0), (10.8, 10.0), (11.3, 0.0)])
    a += 7 * math.exp(-(t - 13.1) * 6) if t >= 13.1 else 0.0
    if a <= 0.01:
        return (0.0, 0.0)
    return (a * (math.sin(t * 53) + 0.5 * math.sin(t * 97)), a * (math.cos(t * 61) + 0.5 * math.sin(t * 83)))


# ------------------------------------------------------------- uzay durumu --

def hiz(t):
    return keys(t, [(8.8, 0.0), (9.4, 1.0), (10.8, 1.0), (11.5, 0.06)])


_travel = []


def yol(t):
    """Yıldızların toplam kayma miktarı (hızın integrali)."""
    if not _travel:
        acc, dt = 0.0, 1 / 240
        for i in range(int(SURE / dt) + 2):
            _travel.append(acc)
            tt = i * dt
            acc += (35 + 3400 * hiz(tt)) * dt
    i = int(t * 240)
    return _travel[min(max(i, 0), len(_travel) - 1)]


def gezegen(t):
    """Brokoli gezegeninin ekran konumu ve yarıçapı."""
    u = ease_in_out(span(t, KARSILASMA, 15.6))
    x = lerp(TARGET[0], 690, u)
    y = lerp(TARGET[1], 560, u)
    r = lerp(14, 300, u ** 1.4) + 30 * smooth(span(t, 15.6, 20.0))
    return x, y, r


# ------------------------------------------------------------------ bölüm --

class Bolum1:
    def __init__(self, out_w=1080, out_h=1920, ss=2):
        self.ow, self.oh, self.ss = out_w, out_h, ss
        self.uzay = Uzay(out_w, out_h, ss)

    def canvas(self, img=None):
        return Canvas(self.ow, self.oh, self.ss, img=img)

    # sahneler -------------------------------------------------------------
    def mutfak_sahnesi(self, t):
        cv = self.canvas()
        b = bebek_poz(t)
        ikinci = t >= GERI[0]
        with cv.push(kamera(t)):
            mutfak(cv, t)
            sandalye_arka(cv, b, 0.0)
            bebek_govde(cv, b)
            sandalye_tepsi(cv, b, 0.0, t, bowl=1.0, spoon=0.0 if ikinci else 1.0)
            bebek_bas(cv, b)
            if t < 2.1:
                # annenin kolları (kameranın olduğu yerden, alttan uzanır)
                rel = ease_in(span(t, 1.35, 2.05))
                for side in (-1, 1):
                    sh = (HEAD[0] + side * 640, 2250)
                    hand = (HEAD[0] + side * 142, HEAD[1] + b.dy + 228)
                    hand = (lerp(hand[0], sh[0], rel * 0.75), lerp(hand[1], sh[1], rel * 0.75))
                    el = ((hand[0] + sh[0]) / 2 + side * 170, (hand[1] + sh[1]) / 2 + 60)
                    anne_kol_pov(cv, sh, el, hand, side, s=1.0)
            bebek_kollar(cv, b)
            if ikinci:
                come = ease_out(span(t, GERI[0], GERI[0] + 0.5))
                ox = (1 - come) * 500
                tip = (705 + 22 * math.sin(t * 2.4) + ox, 828 + 14 * math.sin(t * 3.3))
                hand = (tip[0] + 190, tip[1] + 70)
                anne_kol(cv, 1320 + ox, 1260, hand[0], hand[1], s=1.0, spoon=tip, t=t)
        return cv

    def uzay_sahnesi(self, t, cam=None, gz=None, panel=True):
        cv = self.canvas()
        b = bebek_poz(t)
        sh = sarsinti(t)
        self.uzay.draw(cv, t, speed=hiz(t), drift=(6 * math.sin(t * 0.2), -8 * t), shake=sh, travel=yol(t))
        with cv.screen():
            gx = 180 + 8 * math.sin(t * 0.3) + sh[0] * 0.3
            gy = 400 + (yol(t) - yol(IRIS[0])) * 0.22
            if gy < 2100:
                halkali_gezegen(cv, gx, gy, 52, t)
            my = 1380 + (yol(t) - yol(IRIS[0])) * 0.3
            if my < 2100:
                cv.circle(930 + sh[0] * 0.2, my, 26, fill=(190, 200, 240))
                cv.circle(938 + sh[0] * 0.2, my - 8, 22, fill=(214, 222, 250))
            if t >= HEDEF and t < KARSILASMA + 0.2:
                ap = smooth(span(t, HEDEF, HEDEF + 0.3))
                cv.glow(TARGET[0], TARGET[1], 60, (140, 255, 140), 0.8 * ap)
                cv.circle(TARGET[0], TARGET[1], 10 * ap + 4 * math.sin(t * 9) * ap, fill=(150, 240, 120))
            if t >= KARSILASMA or gz is not None:
                x, y, r = gz if gz is not None else gezegen(t)
                brokoli_gezegen(cv, x + sh[0] * 0.3, y + sh[1] * 0.3, r, t=t, rot=0.08 * math.sin(t * 0.4) - 0.1)
        lean = joystick_lean(t)
        stick = smooth(span(t, 8.05, 8.55))
        thrust = keys(t, [(8.6, 0.0), (8.9, 1.0), (11.0, 1.0), (11.5, 0.0)])
        morph = smooth(span(t, 3.25, 4.4))
        with cv.push(cam if cam is not None else kamera(t)):
            sandalye_arka(cv, b, morph, thrust=thrust, t=t)
            bebek_govde(cv, b)
            sandalye_tepsi(cv, b, morph, t, bowl=1.0, spoon=1.0, stick=stick, lean=lean)
            bebek_bas(cv, b)
            kask_yaka(cv, b)
            bebek_kollar(cv, b)
            kask_fanus(cv, b, t)
        alarm = window(t, 11.6, 13.0, 0.1, 0.3)
        if panel:
            kokpit(cv, t, slide=span(t, 3.7, 4.5), alarm=alarm)
        return cv

    # kare -----------------------------------------------------------------
    def kare(self, t):
        if t < IRIS[0]:
            img = self.mutfak_sahnesi(t).img
        elif t < IRIS[1]:
            img = self._daire(self.mutfak_sahnesi(t).img, self.uzay_sahnesi(t).img,
                              ease_in(span(t, *IRIS)) * 1500 + 1)
        elif t < GERI[0]:
            img = self.uzay_sahnesi(t).img
        elif t < GERI[1]:
            r = (1 - ease_in(span(t, *GERI))) * 1500
            img = self._daire(self.mutfak_sahnesi(t).img, self.uzay_sahnesi(GERI[0] - 0.001).img, r)
        elif t < KAPANIS[0]:
            img = self.mutfak_sahnesi(t).img
        else:
            card = self.canvas()
            kapanis_karti(card, t, KAPANIS[0])
            if t < KAPANIS[1]:
                a = smooth(span(t, *KAPANIS))
                img = Image.blend(self.mutfak_sahnesi(t).img, card.img, a)
            else:
                img = card.img
        cv = self.canvas(img)
        self.ust_katman(cv, t)
        return cv.result()

    def _daire(self, dis, ic, r):
        """'ic' görüntüsünü bebeğin başı merkezli r yarıçaplı daire içinde göster."""
        if r <= 1:
            return dis
        k = self.ow / W * self.ss
        cx, cy = HEAD[0] * k, HEAD[1] * k
        mask = Image.new("L", dis.size, 0)
        ImageDraw.Draw(mask).ellipse((cx - r * k, cy - r * k, cx + r * k, cy + r * k), fill=255)
        return Image.composite(ic, dis, mask)

    # ekran üstü katman -----------------------------------------------------
    def ust_katman(self, cv, t):
        # geçiş parıltıları
        if IRIS[0] <= t < IRIS[1] + 0.2:
            r = ease_in(span(t, *IRIS)) * 1500
            fade = 1 - span(t, IRIS[1], IRIS[1] + 0.2)
            with cv.screen():
                for i in range(18):
                    a = i / 18 * 2 * math.pi + t * 2
                    x, y = HEAD[0] + r * math.cos(a), HEAD[1] + r * math.sin(a)
                    parilti(cv, x, y, 34 + 14 * math.sin(i * 1.3 + t * 9), WHITE, 0.9 * fade, rot=t * 3)
                    cv.glow(x, y, 70, (255, 240, 200), 0.5 * fade)
        if GERI[0] <= t < GERI[1] + 0.35:
            r = (1 - ease_in(span(t, *GERI))) * 1500
            pop = span(t, GERI[1] - 0.05, GERI[1] + 0.35)
            with cv.screen():
                if t < GERI[1]:
                    for i in range(14):
                        a = i / 14 * 2 * math.pi - t * 3
                        parilti(cv, HEAD[0] + r * math.cos(a), HEAD[1] + r * math.sin(a), 30, WHITE, 0.85)
                if pop > 0:
                    for i in range(12):
                        a = i / 12 * 2 * math.pi
                        rr = 40 + 260 * ease_out(pop)
                        cv.circle(HEAD[0] + rr * math.cos(a), HEAD[1] + rr * math.sin(a), 14 * (1 - pop),
                                  fill=rgba((200, 230, 255), 1 - pop))

        # hedef nişangâhı ve uyarı paneli
        if HEDEF <= t < KARSILASMA + 0.3:
            nisangah(cv, TARGET[0], TARGET[1], t, smooth(span(t, HEDEF + 0.05, HEDEF + 0.6)),
                     window(t, HEDEF, KARSILASMA + 0.3, 0.15, 0.3))
        if 11.6 <= t < KARSILASMA:
            hud_uyari(cv, t, 11.6, window(t, 11.6, KARSILASMA, 0.05, 0.25))

        # replikler
        for _, t0, t1, kind, text in REPLIKLER:
            if not (t0 <= t <= t1):
                continue
            ap = span(t, t0, t0 + 0.28)
            al = 1 - span(t, t1 - 0.2, t1)
            if kind == "anne":
                if t0 < 5:
                    konusma_balonu(cv, text, 470, 320, (1040, 380), ap, al)
                else:
                    konusma_balonu(cv, text, 480, 340, (1060, 470), ap, al)
            elif kind == "anlatici":
                altyazi(cv, text, 1560, min(span(t, t0, t0 + 0.35), al))
            elif kind == "bebek":
                konusma_balonu(cv, text, 480, 960, (318, 1092), ap, al, size=52, max_w=700)
            elif kind == "ic_ses":
                dusunce_balonu(cv, text, 540, 400, (470, 650), ap, al, size=56, max_w=640)


# ----------------------------------------------------------------- kapak --

def kapak(bolum, path):
    """Sosyal medya kapak görseli: uzay sahnesi + bölüm başlığı."""
    cam = T(400, 1290) @ S(0.86) @ T(-HEAD[0], -HEAD[1])
    cv = bolum.canvas(bolum.uzay_sahnesi(16.2, cam=cam, gz=(700, 800, 250), panel=False).img)
    from arayuz import INK
    from cizim import text_w
    with cv.screen():
        cv.rrect(60, 150, 1020, 470, 48, fill=rgba((255, 255, 255), 0.92))
        cv.text(540, 238, "MAMA SANDALYESİ Mİ,", 72, INK, weight=700, width=104)
        cv.text(540, 330, "UZAY GEMİSİ Mİ?", 86, (232, 84, 112), weight=700, width=104)
        title = "BEBEĞİN DÜNYASINDA BİR GÜN · BÖLÜM 1"
        tw = text_w(title, 34, 700, 112)
        cv.rrect(540 - tw / 2 - 28, 400, 540 + tw / 2 + 28, 450, 25, fill=(255, 196, 84))
        cv.text(540, 425, title, 34, INK, weight=700, width=112)
    cv.result().convert("RGB").save(path, quality=92)


# ------------------------------------------------------------------ main --

def main(argv=None):
    p = argparse.ArgumentParser(description="Bebeğin Dünyasında Bir Gün · Bölüm 1 videosunu üretir.")
    p.add_argument("--cikti", default=str(HERE / "cikti" / "bolum1_mama_sandalyesi.mp4"))
    p.add_argument("--preview", action="store_true", help="hızlı deneme: 540×960, 15 fps")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--ss", type=int, default=2, help="kenar yumuşatma için süper örnekleme katsayısı")
    p.add_argument("--crf", type=int, default=18)
    p.add_argument("--seslendirme", default=str(HERE / "seslendirme"),
                   help="replik ses dosyalarının klasörü (yoksa yalnızca yazı gösterilir)")
    p.add_argument("--muzik-yok", action="store_true", help="müzik ve efektleri kapat")
    p.add_argument("--kare", type=float, help="yalnızca bu saniyedeki kareyi PNG olarak kaydet")
    p.add_argument("--kapak", action="store_true", help="yalnızca kapak görselini üret")
    a = p.parse_args(argv)

    ow, oh = (540, 960) if a.preview else (1080, 1920)
    fps = 15 if a.preview and a.fps == 30 else a.fps
    out = Path(a.cikti)
    out.parent.mkdir(parents=True, exist_ok=True)
    bolum = Bolum1(ow, oh, a.ss)

    if a.kare is not None:
        path = out.with_name(f"kare_{a.kare:05.2f}.png")
        bolum.kare(a.kare).save(path)
        print(f"Kaydedildi: {path}")
        return
    kapak_path = out.with_suffix(".kapak.jpg")
    kapak(bolum, kapak_path)
    print(f"Kapak: {kapak_path}")
    if a.kapak:
        return

    audio = None
    if not a.muzik_yok or Path(a.seslendirme).is_dir():
        audio = out.with_suffix(".ses.wav")
        bulunan = ses.ses_izi(audio, SURE, REPLIKLER, Path(a.seslendirme), muzik=not a.muzik_yok)
        for name in bulunan:
            print(f"  seslendirme: {name}")
        if not bulunan:
            print("  seslendirme bulunamadı: replikler yalnızca yazı olarak gösterilecek")

    n = int(round(SURE * fps))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{ow}x{oh}", "-r", str(fps), "-i", "-"]
    if audio:
        cmd += ["-i", str(audio)]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf), "-pix_fmt", "yuv420p",
            "-movflags", "+faststart"]
    if audio:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd.append(str(out))
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    try:
        for i in range(n):
            frame = bolum.kare(i / fps)
            proc.stdin.write(frame.tobytes())
            if i % fps == 0 or i == n - 1:
                el = time.time() - t0
                eta = el / (i + 1) * (n - i - 1)
                print(f"\r  kare {i + 1}/{n}  ({(i + 1) / n * 100:4.1f}%)  kalan ~{eta:4.0f} sn", end="", flush=True)
    finally:
        proc.stdin.close()
        proc.wait()
    print()
    if audio:
        audio.unlink(missing_ok=True)
    if proc.returncode != 0:
        sys.exit("ffmpeg video kodlamasında hata verdi.")
    print(f"Video: {out}")


if __name__ == "__main__":
    main()
