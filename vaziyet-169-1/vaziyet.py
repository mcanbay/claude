# -*- coding: utf-8 -*-
"""
Bursa / Nilüfer / İrfaniye, 169 ada 1 + 2 parseller (tevhit): bitişik villa vaziyet planı (ön çalışma)

Varyantlar (VARYANTLAR sözlüğü):
  A: 32 villa, iki kesintisiz blok (16+16), sol uçta dönüş cebi
  B: 32 villa, iki kesintisiz blok (16+16), dönüş cebi yok, villa cephesi en geniş
  C: 32 villa, her sırada 2 blok (8+8), bloklar arası 6 m
  D: 30 villa, her sırada 2 blok (8+7), bloklar arası 6 m
  E: 28 villa, her sırada 3 blok (5+4+5), bloklar arası 6 m
Çıktılar: vaziyet_169-1-2_<V>.pdf / .png / .dxf
PDF: A3 yatay 1/400 pafta. DXF: TM30 (ITRF96, EPSG:5254) koordinatlı.

Çalıştırma: python vaziyet.py          (tüm varyantları üretir)
            python vaziyet.py C
"""
import sys
import math
import re

import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, FancyArrow
from pyproj import Transformer
from shapely import affinity
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union

# ---------------------------------------------------------------- parametreler
KMLS = ["parsel-169-1.kml", "parsel-169-2.kml"]   # tevhit edilecek parseller
CEKME = 3.0          # parsel sınırından bina çekme mesafesi (varsayım; imar durumundan teyit edilmeli)
OTOPARK = 5.0        # her villanın önündeki otopark derinliği
YOL = 6.0            # site içi yol genişliği (çift yön)
BLOK_ARA = 6.0       # ayrık bloklar arasındaki asgari mesafe (iki kütle arası)
W_MAX = 6.60         # villa cephesi üst sınırı (4+1 tip kat planı bu genişliğe göre çizildi)
VARYANTLAR = {
    # ad: (villa derinliği D, sol uçta dönüş cebi, A sırası blokları, B sırası blokları, açıklama)
    "A": (11.5, 6.0, [16], [16], "sol uçta dönüş cebi var"),
    "B": (11.0, 0.0, [16], [16], "dönüş cebi yok, villa cephesi en geniş"),
    "C": (11.0, 0.0, [8, 8], [8, 8], "32 villa, her sırada 2 blok (8+8), bloklar arası 6 m"),
    "D": (11.0, 0.0, [8, 7], [7, 8], "30 villa, her sırada 2 blok (8+7), bloklar arası 6 m"),
    "E": (11.0, 0.0, [5, 4, 5], [5, 4, 5], "28 villa, her sırada 3 blok (5+4+5), bloklar arası 6 m"),
    "F": (11.0, 0.0, [7, 7], [7, 7], "28 villa, kademeli cephe, ortada sosyal meydan (havuz, oyun alanı)"),
    "G": (11.0, 0.0, [16], [16], "32 villa, otopark girişte toplu, iç kısım araçsız lineer park, kademeli cephe"),
    "H": (9.0, 0.0, [2] * 5, [2] * 5, "20 ikiz villa (10 blok), bloklar arası 6 m, villa 8,00 × 9,00 m"),
}
# ek seçenekler: kademe = ikişerli villaların bahçeye doğru geri çekilmesi (m);
# meydan = iki sıradaki blok boşluğunu karşı karşıya hizalayıp genişletir, ortak sosyal alan yapar
# park = iç kısmı araçsız site: her sıranın soldaki n_uzak villasının önünde araç yolu yoktur (ön bahçe + park);
# girişe yakın villaların ön şeridinde 2'şer otopark yeri bulunur (toplu otopark)
VARYANT_OPS = {"F": dict(kademe=1.5, meydan=True),
               "G": dict(kademe=1.5, park=dict(n_uzak=7, on_bahce=2.5, donus=7.0)),
               # ikiz: sabit 8,00 m cephe, blok aralarında misafir otoparkı yok (yan bahçe), her villa önünde 2 araç
               "H": dict(w=8.0, gap_misafir=0, iki_park=True)}
VARYANT = sys.argv[1] if len(sys.argv) > 1 else "A"
D, CEP, BLOK_UST, BLOK_ALT, VARYANT_ACIKLAMA = VARYANTLAR[VARYANT]
N_UST, N_ALT = sum(BLOK_UST), sum(BLOK_ALT)
ARA_UST, ARA_ALT = (len(BLOK_UST) - 1) * BLOK_ARA, (len(BLOK_ALT) - 1) * BLOK_ARA
OPS = VARYANT_OPS.get(VARYANT, {})
KADEME = OPS.get("kademe", 0.0)
PARK_OPS = OPS.get("park")
BALKON = 1.5         # arka balkon çıkması (1. kat, kesikli gösterilir)
BALKON_ON = 1.6      # ön balkon çıkması (1. kat, otopark üstüne; girişe saçak olur)
BRUT = 165.0         # villa başı brüt alan (balkon dahil)
EKSEN_ACI = 69.6     # parsel uzun ekseninin doğudan açısı (derece)

# ---------------------------------------------------------------- parsel
to_tm = Transformer.from_crs(4326, 5254, always_xy=True)
TXTS = [open(k, encoding="utf-8").read() for k in KMLS]


def kml_data(name, txt=None):
    m = re.search(r'<Data name="%s">\s*<value>(.*?)</value>' % name, txt or TXTS[0], re.S)
    return m.group(1).strip() if m else ""


def kml_poly(txt):
    coords = re.search(r"<coordinates>(.*?)</coordinates>", txt, re.S).group(1).split()
    return Polygon([to_tm.transform(*map(float, c.split(",")[:2])) for c in coords])


P_tm = unary_union([kml_poly(t) for t in TXTS]).simplify(0.05)
PARSEL_NO = " + ".join(kml_data("ParselNo", t) for t in TXTS)
OX, OY = P_tm.centroid.x, P_tm.centroid.y
_tmp = affinity.rotate(affinity.translate(P_tm, -OX, -OY), -EKSEN_ACI, origin=(0, 0))
MX, MY = _tmp.bounds[0], _tmp.bounds[1]
PARSEL = affinity.translate(_tmp, -MX, -MY)          # yerel: u uzun eksen, v enine


def to_world(x, y):
    """yerel (u,v) -> TM30 (sağa, yukarı)"""
    x, y = x + MX, y + MY
    a = math.radians(EKSEN_ACI)
    return (x * math.cos(a) - y * math.sin(a) + OX, x * math.sin(a) + y * math.cos(a) + OY)


BUILD = PARSEL.buffer(-CEKME, join_style=2)          # yapı yaklaşma sınırı

# ---------------------------------------------------------------- şeritler (v ekseni)
def seritler(ust_arka):
    ust = (ust_arka - D, ust_arka)
    ust_otp = (ust[0] - OTOPARK, ust[0])
    yol = (ust_otp[0] - YOL, ust_otp[0])
    alt_otp = (yol[0] - OTOPARK, yol[0])
    alt = (alt_otp[0] - D, alt_otp[0])
    return ust, ust_otp, yol, alt_otp, alt


def sol_kenar(v):
    """parsel sol (giriş karşısı) kenarının v yüksekliğindeki x değeri"""
    s = PARSEL.intersection(LineString([(-1, v), (BIG, v)]))
    return s.bounds[0]


def bant(v0, v1, xmin):
    """[v0,v1] bandında yapı yaklaşma sınırı içindeki en sol/en sağ x"""
    xs = [x * 0.05 for x in range(int(xmin / 0.05), 3000)]
    ok = [x for x in xs if BUILD.contains(box(x, v0, x + 0.05, v1))]
    return ok[0], ok[-1] + 0.05


BIG = 200
# en geniş villa cephesini ve iki yandaki bahçeleri dengeleyen yol konumunu ara
_best = None
for _t10 in range(400, 560, 5):
    _ua = _t10 / 10
    _u, _uo, _y, _ao, _a = seritler(_ua)
    _cep_x = (sol_kenar(_uo[1]) + CEP) if CEP else 0.0
    try:
        _su, _sa = bant(*_u, _cep_x), bant(*_a, _cep_x)
    except IndexError:
        continue
    _w = math.floor(min((_su[1] - _su[0] - ARA_UST) / N_UST, (_sa[1] - _sa[0] - ARA_ALT) / N_ALT) * 20) / 20
    _w = min(_w, W_MAX)
    _ust_bahce = PARSEL.bounds[3] - 1.0 - _ua
    _denge = abs(_ust_bahce - _a[0])
    _key = (_w, -_denge)
    if _best is None or _key > _best[0]:
        _best = (_key, _ua, _su, _sa, _cep_x)
(W, _), UST_ARKA, SU, SA, CEP_X = _best
if OPS.get("w"):                      # sabit villa cephesi (ikiz vb.): sığdığını kontrol et
    assert OPS["w"] <= W + 1e-6 or (SU[1] - SU[0] - ARA_UST) / N_UST >= OPS["w"] - 1e-6, "villa cephesi sığmıyor"
    W = OPS["w"]
ust, ust_otp, yol, alt_otp, alt = seritler(UST_ARKA)
# sıraları giriş (sağ) ucuna yaslamak yerine bant içinde ortala
L_UST, L_ALT = N_UST * W + ARA_UST, N_ALT * W + ARA_ALT          # sıra boyları (bloklar + aralar)
X_UST = round(SU[0] + ((SU[1] - SU[0]) - L_UST) / 2, 2)
X_ALT = round(SA[0] + ((SA[1] - SA[0]) - L_ALT) / 2, 2)
GAPS_UST, GAPS_ALT = [BLOK_ARA] * (len(BLOK_UST) - 1), [BLOK_ARA] * (len(BLOK_ALT) - 1)
MEYDAN_U = None
if OPS.get("meydan"):
    # iki sıranın boşluğunu aynı u aralığına getir; en geniş boşluğu, dengeli bölünmeyi ve orta konumu ara
    _best_m = None
    _mid = (max(SU[0], SA[0]) + min(SU[1], SA[1])) / 2
    for _uc10 in range(int(min(SU[0], SA[0]) * 10), int(max(SU[1], SA[1]) * 10)):
        _uc = _uc10 / 10
        for _g10 in range(200, int(BLOK_ARA * 10) - 1, -1):
            _g = _g10 / 10
            _spl = []
            for (_b0, _b1), _n in ((SU, N_UST), (SA, N_ALT)):
                _c = [k for k in range(2, _n - 1) if _uc - _g / 2 - k * W >= _b0 - 1e-6
                      and _uc + _g / 2 + (_n - k) * W <= _b1 + 1e-6]
                if not _c:
                    break
                _spl.append(min(_c, key=lambda k: abs(k - _n / 2)))
            if len(_spl) == 2:
                _key = (_g, -sum(abs(k - n / 2) for k, n in zip(_spl, (N_UST, N_ALT))), -abs(_uc - _mid))
                if _best_m is None or _key > _best_m[0]:
                    _best_m = (_key, _uc, _g, _spl)
                break
    _, _uc, _g, (_ka, _kb) = _best_m
    BLOK_UST, BLOK_ALT = [_ka, N_UST - _ka], [_kb, N_ALT - _kb]
    GAPS_UST = GAPS_ALT = [_g]
    X_UST, X_ALT = _uc - _g / 2 - _ka * W, _uc - _g / 2 - _kb * W
    L_UST, L_ALT = N_UST * W + _g, N_ALT * W + _g
    MEYDAN_U = (_uc - _g / 2, _uc + _g / 2)

villas = []   # dict: no, ev, otopark, park_yeri, yuruyus, bahce, balkon, sira, blok, blok_bas, blok_son
ARALAR = []   # dict: sira, u0, u1 (bloklar arası 6 m boşluk)
MISAFIR = []  # misafir otoparkı yerleri (bloklar arasındaki boşluğun ön şeridinde)


def make_row(x0, n, ev, otp, bahce_side, no0, sira, blok=0):
    for k in range(n):
        x = x0 + k * W
        # kademe: ikişerli gruplar dönüşümlü olarak bahçeye doğru KADEME kadar geri çekilir
        d = KADEME if (k // 2) % 2 == 1 else 0.0
        dv = d if bahce_side == "ust" else -d
        ev_k = (ev[0] + dv, ev[1] + dv)
        house = box(x, ev_k[0], x + W, ev_k[1])
        front = box(x, otp[0], x + W, otp[1])
        on_bahce = (box(x, ev[0], x + W, ev_k[0]) if bahce_side == "ust" else box(x, ev_k[1], x + W, ev[1])) \
            if d else Polygon()
        # park yerleri çiftler halinde yan yana (ortak bordür kesimi)
        left = (k % 2 == 1)
        sx = x if left else x + W - 2.6
        stall = box(sx, otp[0], sx + 2.6, otp[1])
        wx = x + W - 1.4 if left else x + 0.2
        # yürüyüş yolu otopark şeridinden (kademeli villada ön bahçeyi geçerek) kapıya ulaşır
        walk = box(wx, otp[0], wx + 1.2, ev_k[0]) if bahce_side == "ust" else box(wx, ev_k[1], wx + 1.2, otp[1])
        uzak = bool(PARK_OPS) and k < PARK_OPS["n_uzak"]
        parklar = [stall]
        if PARK_OPS and uzak:
            # araçsız kısım: otopark yok; ev önünde özel ön bahçe, parka açılan kapı ve yürüyüş yolu
            ob = PARK_OPS["on_bahce"]
            pk = otp[1] - ob if bahce_side == "ust" else otp[0] + ob     # park kenarı
            on_bahce = box(x, pk, x + W, ev_k[0]) if bahce_side == "ust" else box(x, ev_k[1], x + W, pk)
            walk = box(wx, pk, wx + 1.2, ev_k[0]) if bahce_side == "ust" else box(wx, ev_k[1], wx + 1.2, pk)
            stall, front = Polygon(), Polygon()
            parklar = []
        elif PARK_OPS or OPS.get("iki_park"):
            # ön şeritte yürüyüş yolunun yanında 2 araçlık yer (G: biri uzak villalara tahsisli; H: villanın kendi 2 aracı)
            s0 = x + 1.45 if not left else x
            parklar = [box(s0, otp[0], s0 + 2.55, otp[1]), box(s0 + 2.55, otp[0], s0 + 5.1, otp[1])]
            stall = unary_union(parklar)
        e0, e1 = ev_k
        if bahce_side == "ust":
            g = box(x, e1, x + W, BIG).intersection(PARSEL)
            bal = box(x + 0.1, e1, x + W - 0.1, e1 + BALKON)
            bal_on = box(x + 0.1, e0 - BALKON_ON, x + W - 0.1, e0)
        else:
            g = box(x, -BIG, x + W, e0).intersection(PARSEL)
            bal = box(x + 0.1, e0 - BALKON, x + W - 0.1, e0)
            bal_on = box(x + 0.1, e1, x + W - 0.1, e1 + BALKON_ON)
        villas.append(dict(no=no0 + k, ev=house, otopark=front, park=stall, yuruyus=walk,
                           bahce=g, on_bahce=on_bahce, balkon=bal, balkon_on=bal_on, sira=sira, blok=blok,
                           blok_bas=(k == 0), blok_son=(k == n - 1), kademe=d, uzak=uzak, parklar=parklar))


def make_bloklar(x0, bloklar, ev, otp, bahce_side, no0, sira, aralar=None):
    """Sırayı bloklara böler; bloklar arasında boşluk bırakır (asgari BLOK_ARA). Normal boşlukta yarısı
    komşu uç villanın yan bahçesi olur, ön şeridine iki misafir otoparkı konur. Meydan boşluğu ortak alandır."""
    aralar = aralar or [BLOK_ARA] * (len(bloklar) - 1)
    x = x0
    for b, n in enumerate(bloklar):
        make_row(x, n, ev, otp, bahce_side, no0, sira, blok=b)
        no0 += n
        x += n * W
        if b < len(bloklar) - 1 and MEYDAN_U:
            ARALAR.append(dict(sira=sira, u0=x, u1=x + aralar[b], meydan=True))
            x += aralar[b]
            continue
        if b < len(bloklar) - 1:
            gu0, gu1 = x, x + aralar[b]
            gc = (gu0 + gu1) / 2
            ARALAR.append(dict(sira=sira, u0=gu0, u1=gu1))
            for a0 in (gc - 2.55, gc + 0.05)[:OPS.get("gap_misafir", 2)]:
                MISAFIR.append(box(a0, otp[0], a0 + 2.5, otp[1]))
            # yan bahçeler: uç villanın yanında, ön cephe hizasından bahçe sonuna kadar
            for vv in villas:
                if vv["sira"] != sira:
                    continue
                hu0, hv0, hu1, hv1 = vv["ev"].bounds
                if abs(hu1 - gu0) < 1e-6:          # boşluğun solundaki villa
                    yan = box(hu1, hv0, gc, hv1)
                    arka = box(hu1, hv1, gc, BIG) if bahce_side == "ust" else box(hu1, -BIG, gc, hv0)
                    vv["bahce"] = unary_union([vv["bahce"], yan, arka.intersection(PARSEL)])
                    vv["lot_u1"] = gc
            x += aralar[b]
    # boşluğun sağındaki villalar (bir sonraki bloğun ilk villası)
    for a in [a for a in ARALAR if a["sira"] == sira and not a.get("meydan")]:
        gc = (a["u0"] + a["u1"]) / 2
        for vv in villas:
            hu0, hv0, hu1, hv1 = vv["ev"].bounds
            if vv["sira"] == sira and abs(hu0 - a["u1"]) < 1e-6:
                yan = box(gc, hv0, hu0, hv1)
                arka = box(gc, hv1, hu0, BIG) if bahce_side == "ust" else box(gc, -BIG, hu0, hv0)
                vv["bahce"] = unary_union([vv["bahce"], yan, arka.intersection(PARSEL)])
                vv["lot_u0"] = gc


# numaralandırma girişten (sağ uç) başlar: A sırası sağdan sola V1.., B sırası soldan sağa
make_bloklar(X_UST, BLOK_UST, ust, ust_otp, "ust", 1, "A", GAPS_UST)
for i, v in enumerate(reversed(villas)):
    v["no"] = i + 1
make_bloklar(X_ALT, BLOK_ALT, alt, alt_otp, "alt", N_UST + 1, "B", GAPS_ALT)

YOL_POLY = box(-BIG, yol[0], BIG, yol[1]).intersection(PARSEL)
PARK = {}
if PARK_OPS:
    # otopark yolu, girişe yakın villaların başladığı yerden girişe kadar; ucunda dönüş meydanı
    _lot0 = max(min(v["ev"].bounds[0] for v in villas if v["sira"] == r and not v["uzak"]) for r in ("A", "B"))
    _ob, _dn = PARK_OPS["on_bahce"], PARK_OPS["donus"]
    _pk_alt, _pk_ust = alt_otp[0] + _ob, ust_otp[1] - _ob                 # parkın iki kenarı (v)
    _donus = box(_lot0 - _dn, _pk_alt, _lot0, _pk_ust).intersection(PARSEL)
    YOL_POLY = unary_union([box(_lot0, yol[0], BIG, yol[1]).intersection(PARSEL), _donus])
    _ic = PARSEL.buffer(-0.25, join_style=2)
    _park = box(-BIG, _pk_alt, _lot0 - _dn, _pk_ust).intersection(_ic)
    _pu0, _, _pu1, _ = _park.bounds
    _ser = 3.5                                                            # acil durum / yaya yolu
    _lane = box(_pu0, _pk_alt, _pu1, _pk_alt + _ser).intersection(_park)
    _z0, _z1 = _pk_alt + _ser, _pk_ust                                     # donatı şeridi
    _perg = box(_pu1 - 8.0, _z0 + 1.0, _pu1 - 2.0, _z1 - 1.0)
    _oyun = box(_pu1 - 21.0, _z0 + 0.6, _pu1 - 9.5, _z1 - 0.6)
    _hobi = [box(_pu1 - 31.0 + i * 3.0, _z0 + 1.5, _pu1 - 29.0 + i * 3.0, _z1 - 1.5) for i in range(3)]
    PARK = dict(
        alan=_park, serit=_lane, donus=_donus, pergola=_perg, oyun=_oyun, hobi=_hobi,
        bank=[box(_perg.bounds[0] + 0.5, _perg.bounds[1] + 0.3, _perg.bounds[0] + 2.3, _perg.bounds[1] + 0.8),
              box(_perg.bounds[2] - 2.3, _perg.bounds[1] + 0.3, _perg.bounds[2] - 0.5, _perg.bounds[1] + 0.8),
              box(_perg.bounds[0] + 0.5, _perg.bounds[3] - 0.8, _perg.bounds[0] + 2.3, _perg.bounds[3] - 0.3),
              box(_perg.bounds[2] - 2.3, _perg.bounds[3] - 0.8, _perg.bounds[2] - 0.5, _perg.bounds[3] - 0.3)],
        oyun_ekipman=[box(_oyun.bounds[0] + 1.0, _oyun.bounds[1] + 1.0, _oyun.bounds[0] + 4.0, _oyun.bounds[1] + 3.5),
                      box(_oyun.bounds[0] + 5.5, _oyun.bounds[3] - 2.4, _oyun.bounds[0] + 8.5, _oyun.bounds[3] - 1.0),
                      box(_oyun.bounds[2] - 2.6, _oyun.bounds[1] + 1.2, _oyun.bounds[2] - 0.8, _oyun.bounds[1] + 3.2)],
        cim=box(_pu0, _z0, _pu1 - 32.0, _z1).intersection(_park),
        agaclar=[(u_, _z1 - 0.9) for u_ in [_pu1 - 1.0 - i * 7.0 for i in range(int((_pu1 - _pu0 - 2) / 7.0) + 1)]]
                + [(u_, _pk_alt + _ser + 0.9) for u_ in [_pu1 - 36.0 - i * 8.0 for i in range(3)] if u_ > _pu0 + 2],
        cop=box(_lot0 - _dn + 0.3, _pk_ust - 2.3, _lot0 - _dn + 3.3, _pk_ust - 0.3),
        bisiklet=box(_lot0 - _dn + 3.6, _pk_ust - 1.8, _lot0 - 0.4, _pk_ust - 0.3),
        babalar=[(_lot0 - _dn, _pk_alt + 0.6 + i * 0.9) for i in range(4)],
        lot0=_lot0,
    )
CEP_POLY = box(-BIG, alt_otp[0], min(X_UST, X_ALT), ust_otp[1]).intersection(PARSEL) if CEP else Polygon()
OTOPARK_SAYI = sum(len(v["parklar"]) for v in villas)
if CEP:
    YOL_POLY = unary_union([YOL_POLY, CEP_POLY])
SETBACK_LINE = BUILD.exterior

# ---------------------------------------------------------------- sosyal meydan (F)
MEYDAN = {}
if MEYDAN_U:
    _g0, _g1 = MEYDAN_U
    _uc = (_g0 + _g1) / 2
    _ic = PARSEL.buffer(-0.25, join_style=2)
    _A = box(_g0, ust_otp[0], _g1, BIG).intersection(_ic)            # yolun A yakası (oyun + pergola)
    _B = box(_g0, -BIG, _g1, alt_otp[1]).intersection(_ic)            # yolun B yakası (havuz)
    _vb0 = _B.bounds[1]
    _va1 = _A.bounds[3]
    # misafir otoparkları: her yakanın ön şeridinde 3 araç, iki yakada karşılıklı uçlarda
    for i in range(3):
        MISAFIR.append(box(_g0 + 0.3 + i * 2.5, alt_otp[0], _g0 + 0.3 + (i + 1) * 2.5, alt_otp[1]))
        MISAFIR.append(box(_g1 - 0.3 - (i + 1) * 2.5, ust_otp[0], _g1 - 0.3 - i * 2.5, ust_otp[1]))
    _hv0 = max(_vb0 + 2.5, alt_otp[0] - 2.0 - 14.0)                   # havuz terası (deck) alt ucu
    deck = box(_uc - 3.9, _hv0, _uc + 3.9, _hv0 + 14.0)
    havuz = box(_uc - 2.25, _hv0 + 2.0, _uc + 2.25, _hv0 + 12.0)
    oyun = box(_g0 + 1.0, ust_otp[1] + 2.0, _g1 - 1.0, ust_otp[1] + 10.0)
    perg_zemin = box(_g0 + 1.5, ust_otp[1] + 11.5, _g1 - 1.5, min(ust_otp[1] + 16.5, _va1 - 1.5))
    pergola = box(_uc - 3.0, perg_zemin.bounds[1] + 0.5, _uc + 3.0, perg_zemin.bounds[3] - 0.5)
    MEYDAN = dict(
        A=_A, B=_B, gecit=box(_g0, yol[0], _g1, yol[1]),
        kaplama=[box(_g0 + 8.1, alt_otp[0], _g1, alt_otp[1]),             # B ön şerit giriş
                 box(_uc - 1.0, deck.bounds[3], _uc + 1.0, alt_otp[0]),    # havuza yürüyüş
                 box(_g0, ust_otp[0], _g1 - 8.1, ust_otp[1]),              # A ön şerit giriş
                 box(_uc - 1.0, ust_otp[1], _uc + 1.0, oyun.bounds[1]),    # oyun alanına yürüyüş
                 box(_uc - 1.0, oyun.bounds[3], _uc + 1.0, perg_zemin.bounds[1]),
                 perg_zemin],
        deck=deck, havuz=havuz, cit=deck.buffer(0.35, join_style=2), oyun=oyun, pergola=pergola,
        sezlong=[box(_uc - 3.65, y, _uc - 2.85, y + 1.9) for y in (_hv0 + 2.5, _hv0 + 5.0, _hv0 + 7.5)]
                + [box(_uc + 2.85, y, _uc + 3.65, y + 1.9) for y in (_hv0 + 2.5, _hv0 + 5.0, _hv0 + 7.5)],
        bank=[box(_uc - 2.5, pergola.bounds[1] + 0.4, _uc - 0.7, pergola.bounds[1] + 0.9),
              box(_uc + 0.7, pergola.bounds[1] + 0.4, _uc + 2.5, pergola.bounds[1] + 0.9),
              box(_uc - 2.5, pergola.bounds[3] - 0.9, _uc - 0.7, pergola.bounds[3] - 0.4),
              box(_uc + 0.7, pergola.bounds[3] - 0.9, _uc + 2.5, pergola.bounds[3] - 0.4)],
        oyun_ekipman=[box(_uc - 3.5, oyun.bounds[1] + 1.5, _uc - 0.5, oyun.bounds[1] + 4.0),   # kule + kaydırak
                      box(_uc + 1.0, oyun.bounds[1] + 1.0, _uc + 4.0, oyun.bounds[1] + 2.4),   # salıncak
                      box(_uc + 1.5, oyun.bounds[1] + 4.5, _uc + 3.5, oyun.bounds[1] + 6.5)],  # kum havuzu
        agaclar=[(_g0 + 1.6, _vb0 + 1.6), (_g1 - 1.6, _vb0 + 1.6), (_g0 + 1.6, _hv0 + 7.0), (_g1 - 1.6, _hv0 + 7.0),
                 (_g0 + 1.6, _va1 - 1.6), (_g1 - 1.6, _va1 - 1.6), (_g0 + 1.4, perg_zemin.bounds[1] - 0.7),
                 (_g1 - 1.4, perg_zemin.bounds[1] - 0.7)],
    )

# ortak alan = parsel - (yol + villa lotları + misafir otoparkları)
lots = unary_union([unary_union([v["ev"], v["otopark"], v["bahce"], v["on_bahce"]]) for v in villas])
ORTAK = PARSEL.difference(unary_union([lots, YOL_POLY] + MISAFIR))

# ---------------------------------------------------------------- mahremiyet duvarları
# Komşu villalar arasında: arka bahçede teras boyunca yüksek, bahçe sonuna kadar alçak duvar;
# 1. katta balkonlar arasında saçağa kadar yan duvar; önde iki giriş yolu yan yana gelen sınırda alçak duvar.
MAH_T = 0.20            # duvar kalınlığı
MAH_TERAS = 3.5         # arka cepheden itibaren yüksek (teras) duvar boyu
MAH_H_TERAS, MAH_H_BAHCE, MAH_H_ON = 2.4, 1.9, 1.4
MAH_ON_BOY = 4.0        # ön bahçede giriş yolları arasındaki duvar boyu
CEVRE_DUVAR_KAL = 0.25  # parsel çevre duvarı kalınlığı
MAH = []                # dict: tip (teras / bahce / on / balkon), poly, h (yükseklik; balkon için saçağa kadar)


def _vband(a, b, u0, u1):
    return box(u0, min(a, b), u1, max(a, b))


def _mahremiyet_duvarlari():
    ic = PARSEL.buffer(-CEVRE_DUVAR_KAL, join_style=2)
    for row, blok in sorted({(v["sira"], v["blok"]) for v in villas}):
        vs = sorted([v for v in villas if v["sira"] == row and v["blok"] == blok], key=lambda v: v["ev"].bounds[0])
        for i, v in enumerate(vs):
            u0, v0, u1, v1 = v["ev"].bounds
            arka, on = (v1, v0) if row == "A" else (v0, v1)
            dis = 1 if row == "A" else -1           # arka cepheden bahçeye doğru v yönü
            # blok sonundaki villanın dış yanında boşluk varsa yan bahçe duvarı boşluğun ortasındadır
            for lot_key, uh in (("lot_u0", u0), ("lot_u1", u1)):
                if lot_key in v:
                    gc = v[lot_key]
                    ln = LineString([(gc, on), (gc, arka + dis * 500)]).intersection(ic)
                    MAH.append(dict(tip="bahce", poly=ln.buffer(MAH_T / 2, cap_style=2), h=MAH_H_BAHCE))
                    MAH.append(dict(tip="on", poly=box(min(uh, gc), on - MAH_T / 2, max(uh, gc), on + MAH_T / 2),
                                    h=MAH_H_ON))
            for uu in [u0] + ([u1] if i == len(vs) - 1 else []):
                if (uu == u0 and "lot_u0" in v) or (uu == u1 and "lot_u1" in v):
                    continue                        # yan bahçeli uç: zemin duvarı boşluğun ortasında
                # kademede duvar, bahçeye daha az taşan (yola yakın) arka cepheden başlar
                arka_d = arka
                if uu == u0 and i > 0:
                    oa = vs[i - 1]["ev"].bounds[3] if row == "A" else vs[i - 1]["ev"].bounds[1]
                    arka_d = min(arka, oa) if row == "A" else max(arka, oa)
                ln = LineString([(uu, arka_d), (uu, arka_d + dis * 500)]).intersection(ic)
                if not ln.is_empty:
                    duvar = ln.buffer(MAH_T / 2, cap_style=2)
                    teras = _vband(arka_d, max(arka, arka_d) + MAH_TERAS if dis > 0 else min(arka, arka_d) - MAH_TERAS,
                                   uu - 1, uu + 1)
                    MAH.append(dict(tip="teras", poly=duvar.intersection(teras), h=MAH_H_TERAS))
                    MAH.append(dict(tip="bahce", poly=duvar.difference(teras), h=MAH_H_BAHCE))
            if i > 0:
                once = vs[i - 1]
                ou0, _, ou1, _ = once["ev"].bounds
                if v["yuruyus"].centroid.x < (u0 + u1) / 2 and once["yuruyus"].centroid.x > (ou0 + ou1) / 2:
                    MAH.append(dict(tip="on", poly=_vband(on, on - dis * MAH_ON_BOY,
                                                          u0 - MAH_T / 2, u0 + MAH_T / 2), h=MAH_H_ON))


_mahremiyet_duvarlari()
if PARK_OPS:
    for _v in villas:
        if not _v["uzak"]:
            continue
        _u0, _v0, _u1, _v1 = _v["ev"].bounds
        _wb = _v["yuruyus"].bounds
        _pk = _wb[1] if _v["sira"] == "A" else _wb[3]                   # park kenarı
        _on = _v0 if _v["sira"] == "A" else _v1
        for _uu in (_u0, _u1):
            MAH.append(dict(tip="on", poly=_vband(_on, _pk, _uu - MAH_T / 2, _uu + MAH_T / 2), h=1.0))
        for _a, _b in ((_u0, _wb[0]), (_wb[2], _u1)):                  # bahçe kapısı yürüyüş yolunda açık
            if _b - _a > 0.05:
                MAH.append(dict(tip="on", poly=box(_a, _pk - MAH_T / 2, _b, _pk + MAH_T / 2), h=1.0))
# 1. kat balkon yan duvarları: her villanın iki yanında, kendi ön ve arka cephesine göre (kademede ayrı ayrı)
_fin_seen = set()
for _v in villas:
    _u0, _v0, _u1, _v1 = _v["ev"].bounds
    _arka, _on = (_v1, _v0) if _v["sira"] == "A" else (_v0, _v1)
    _dis = 1 if _v["sira"] == "A" else -1
    for _uu in (_u0, _u1):
        for _a, _b in ((_arka, _arka + _dis * (BALKON + 0.1)), (_on, _on - _dis * (BALKON_ON + 0.1))):
            _k = (round(_uu, 2), round(min(_a, _b), 2), round(max(_a, _b), 2))
            if _k in _fin_seen:
                continue
            _fin_seen.add(_k)
            MAH.append(dict(tip="balkon", poly=_vband(_a, _b, _uu - MAH_T / 2, _uu + MAH_T / 2), h=None))

# ---------------------------------------------------------------- kontroller / tablo
for v in villas:
    assert BUILD.contains(v["ev"]), v["no"]
    assert v["otopark"].is_empty or PARSEL.buffer(0.01).contains(v["otopark"]), v["no"]
tapu_alanlar = [float(kml_data("Alan", t).replace(".", "").replace(",", ".")) for t in TXTS]
tapu_alan = sum(tapu_alanlar)
geo_alan = PARSEL.area
oturum = W * D
taban_top = oturum * len(villas)
brut_top = BRUT * len(villas)
balkon_villa = BRUT - 2 * oturum
yol_alan = YOL_POLY.area
otopark_alan = sum(v["otopark"].area for v in villas)
bahce_alan = sum(v["bahce"].area for v in villas)
ortak_alan = ORTAK.area
bahce_min = min(v["bahce"].area for v in villas)
bahce_max = max(v["bahce"].area for v in villas)

ozet = [
    ("Parsel alanı (tapu)", f"{tapu_alan:,.2f} m² ({' + '.join(f'{a:,.2f}' for a in tapu_alanlar)})"),
    ("Villa sayısı", f"{len(villas)} adet (A sırası {N_UST} + B sırası {N_ALT})"),
    ("Villa tipi", f"{W:.2f} × {D:.2f} m, " + ("ikiz" if set(BLOK_UST + BLOK_ALT) == {2} else
                                                "blok içinde bitişik" if ARALAR else "bitişik nizam") + ", Z+1"),
    ("Taban oturumu / villa", f"{oturum:.1f} m²"),
    ("Brüt alan / villa", f"{BRUT:.0f} m² (2 × {oturum:.1f} + {balkon_villa:.1f} balkon/teras)"),
    ("Toplam taban oturumu", f"{taban_top:,.0f} m²  →  TAKS ≈ {taban_top / tapu_alan:.2f}"),
    ("Toplam brüt inşaat", f"{brut_top:,.0f} m²  →  KAKS ≈ {brut_top / tapu_alan:.2f}"),
    ("Blok düzeni", f"A: {'+'.join(map(str, BLOK_UST))}, B: {'+'.join(map(str, BLOK_ALT))}"
                    + ((f", ortada {MEYDAN_U[1] - MEYDAN_U[0]:.1f} m meydan".replace(".", ",") if MEYDAN_U else
                        f", bloklar arası {BLOK_ARA:.0f} m") if ARALAR else ", kesintisiz")
                    + (f"; ikişerli {KADEME:.1f} m kademe".replace(".", ",") if KADEME else "")),
    ("Otopark", (f"{OTOPARK_SAYI} yer, girişe yakın villaların önünde 2'şer ({len(villas)} + "
                 f"{OTOPARK_SAYI - len(villas)} misafir)") if PARK else
                f"{OTOPARK_SAYI} yer, her villanın önünde 2 araç" if OPS.get("iki_park") else
                (f"{len(villas)} villa önünde" + (f" + {len(MISAFIR)} misafir" if MISAFIR else "") + " (2,6 × 5,0 m)")),
    ("Otopark yolu" if PARK else "Site içi yol", f"{YOL:.1f} m genişlik, {yol_alan:,.0f} m²" + (" (dönüş cebi dahil)" if CEP else "")),
    ("Özel bahçeler", f"{bahce_alan:,.0f} m² (villa başı {bahce_min:.0f}–{bahce_max:.0f} m²)"),
] + ([("Sosyal meydan", f"{MEYDAN['A'].area + MEYDAN['B'].area:,.0f} m²: havuz, oyun alanı, pergola")]
     if MEYDAN else []) + ([("Araçsız lineer park", f"{PARK['alan'].area:,.0f} m²: oyun, pergola, hobi bahçesi, çim")]
     if PARK else []) + [
    ("Ortak alan / artık", f"{ortak_alan:,.0f} m²"),
]

# ---------------------------------------------------------------- çizim (matplotlib)
C = dict(parsel="#1f2937", cekme="#dc2626", yol="#d6d3d1", otopark="#e7e5e4", park="#a8a29e",
         ev="#b45309", ev_fill="#fde68a", bahce="#dcfce7", ortak="#bbf7d0", yazi="#111827",
         mah="#44403c")


def draw_poly(ax, g, **kw):
    if g.is_empty:
        return
    geoms = getattr(g, "geoms", [g])
    for p in geoms:
        if p.geom_type != "Polygon":
            continue
        ax.add_patch(MPoly(list(p.exterior.coords), closed=True, **kw))


def render(path_pdf, path_png):
    A3 = (420 / 25.4, 297 / 25.4)
    fig = plt.figure(figsize=A3)
    # 1/400: 1 m = 2,5 mm
    MM = 2.5
    pad = 6.0
    x0, y0, x1, y1 = PARSEL.bounds
    wm, hm = (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad
    ax_w, ax_h = wm * MM / 420, hm * MM / 297
    ax = fig.add_axes([20 / 420, 1 - 18 / 297 - ax_h, ax_w, ax_h])
    ax.set_xlim(x0 - pad, x1 + pad)
    ax.set_ylim(y0 - pad, y1 + pad)
    ax.set_aspect("equal")
    ax.axis("off")

    draw_poly(ax, ORTAK, facecolor=C["ortak"], edgecolor="none", zorder=1)
    for v in villas:
        draw_poly(ax, v["bahce"], facecolor=C["bahce"], edgecolor="#86efac", lw=0.4, zorder=1)
        draw_poly(ax, v["otopark"], facecolor=C["otopark"], edgecolor="#a8a29e", lw=0.3, zorder=2)
        for pp in v["parklar"]:
            draw_poly(ax, pp, facecolor=C["park"], edgecolor="#78716c", lw=0.3, zorder=3)
        draw_poly(ax, v["yuruyus"], facecolor="#ffffff", edgecolor="#a8a29e", lw=0.3, zorder=3)
        draw_poly(ax, v["ev"], facecolor=C["ev_fill"], edgecolor=C["ev"], lw=0.8, zorder=4)
    for v in villas:
        draw_poly(ax, v["on_bahce"], facecolor=C["bahce"], edgecolor="#86efac", lw=0.3, zorder=2)
    if MEYDAN:
        M = MEYDAN
        for k in ("A", "B"):
            draw_poly(ax, M[k], facecolor="#c7e9b4", edgecolor="#4d7c0f", lw=0.6, zorder=2)
        draw_poly(ax, M["gecit"], facecolor="#e7dcc8", edgecolor="#a8a29e", lw=0.5, zorder=3, hatch="..")
        for kp in M["kaplama"]:
            draw_poly(ax, kp, facecolor="#e7e1d6", edgecolor="#a8a29e", lw=0.3, zorder=3)
        draw_poly(ax, M["deck"], facecolor="#d6b98c", edgecolor="#8a6d3b", lw=0.4, zorder=3)
        draw_poly(ax, M["havuz"], facecolor="#7cc4e4", edgecolor="#1e6f93", lw=0.7, zorder=4)
        cx, cy = M["cit"].exterior.xy
        ax.plot(cx, cy, color="#1e6f93", lw=0.5, ls=(0, (3, 2)), zorder=4)
        draw_poly(ax, M["oyun"], facecolor="#f4c08a", edgecolor="#b45309", lw=0.5, zorder=3)
        for e in M["oyun_ekipman"]:
            draw_poly(ax, e, facecolor="#fde7cf", edgecolor="#b45309", lw=0.4, zorder=4)
        draw_poly(ax, M["pergola"], facecolor="none", edgecolor="#57534e", lw=0.6, zorder=5)
        pb = M["pergola"].bounds
        for xx in [pb[0] + i * 0.5 for i in range(1, int((pb[2] - pb[0]) / 0.5))]:
            ax.plot([xx, xx], [pb[1], pb[3]], color="#78716c", lw=0.3, zorder=5)
        for b_ in M["bank"] + M["sezlong"]:
            draw_poly(ax, b_, facecolor="#f5f5f4", edgecolor="#57534e", lw=0.3, zorder=5)
        for tx, ty in M["agaclar"]:
            ax.add_patch(plt.Circle((tx, ty), 1.3, fc="#86b86b", ec="#3f6212", lw=0.5, alpha=0.9, zorder=6))
        hb, ob = M["havuz"].bounds, M["oyun"].bounds
        ax.text((hb[0] + hb[2]) / 2, (hb[1] + hb[3]) / 2, "HAVUZ\n4,5 × 10", ha="center", va="center", fontsize=5.5,
                color="#0c4a6e", zorder=7, rotation=90)
        ax.text((ob[0] + ob[2]) / 2, ob[3] - 0.9, "ÇOCUK OYUN ALANI", ha="center", va="center", fontsize=5.5,
                color="#7c2d12", zorder=7)
        ax.text((pb[0] + pb[2]) / 2, (pb[1] + pb[3]) / 2, "PERGOLA", ha="center", va="center", fontsize=5.5,
                color="#292524", zorder=7, bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.8))
        gb = M["gecit"].bounds
        ax.text((gb[0] + gb[2]) / 2, (gb[1] + gb[3]) / 2, "YÜKSELTİLMİŞ\nYAYA GEÇİDİ", ha="center", va="center",
                fontsize=5, color="#44403c", zorder=7, bbox=dict(fc="#e7dcc8", ec="none", pad=0.3))
    if PARK:
        K = PARK
        draw_poly(ax, K["alan"], facecolor="#c7e9b4", edgecolor="#4d7c0f", lw=0.6, zorder=2)
        draw_poly(ax, K["serit"], facecolor="#ddd8cc", edgecolor="#a8a29e", lw=0.4, zorder=3, hatch="..")
        draw_poly(ax, K["donus"], facecolor="#e7e1d6", edgecolor="#a8a29e", lw=0.5, zorder=3)
        draw_poly(ax, K["oyun"], facecolor="#f4c08a", edgecolor="#b45309", lw=0.5, zorder=3)
        for e in K["oyun_ekipman"]:
            draw_poly(ax, e, facecolor="#fde7cf", edgecolor="#b45309", lw=0.4, zorder=4)
        draw_poly(ax, K["pergola"], facecolor="#e7e1d6", edgecolor="#57534e", lw=0.6, zorder=4)
        pb = K["pergola"].bounds
        for xx in [pb[0] + i * 0.5 for i in range(1, int((pb[2] - pb[0]) / 0.5))]:
            ax.plot([xx, xx], [pb[1], pb[3]], color="#78716c", lw=0.3, zorder=5)
        for b_ in K["bank"]:
            draw_poly(ax, b_, facecolor="#f5f5f4", edgecolor="#57534e", lw=0.3, zorder=5)
        for hb_ in K["hobi"]:
            draw_poly(ax, hb_, facecolor="#a16207", edgecolor="#713f12", lw=0.4, zorder=4)
        draw_poly(ax, K["cop"], facecolor="#a8a29e", edgecolor="#44403c", lw=0.4, zorder=4)
        draw_poly(ax, K["bisiklet"], facecolor="#e2e8f0", edgecolor="#64748b", lw=0.4, zorder=4)
        for bx_, by_ in K["babalar"]:
            ax.add_patch(plt.Circle((bx_, by_), 0.15, fc="#44403c", ec="none", zorder=6))
        for tx, ty in K["agaclar"]:
            ax.add_patch(plt.Circle((tx, ty), 1.2, fc="#86b86b", ec="#3f6212", lw=0.5, alpha=0.9, zorder=6))
        ob_, hbb = K["oyun"].bounds, K["hobi"][0].bounds
        ax.text((ob_[0] + ob_[2]) / 2, (ob_[1] + ob_[3]) / 2, "ÇOCUK OYUN", ha="center", va="center", fontsize=5,
                color="#7c2d12", zorder=7)
        ax.text((pb[0] + pb[2]) / 2, (pb[1] + pb[3]) / 2, "PERGOLA", ha="center", va="center", fontsize=5,
                color="#292524", zorder=7, bbox=dict(fc="white", ec="none", pad=0.3, alpha=0.8))
        ax.text((K["hobi"][0].bounds[0] + K["hobi"][-1].bounds[2]) / 2, hbb[3] + 0.6, "HOBİ BAHÇESİ", ha="center",
                fontsize=5, color="#713f12", zorder=7)
        cb_ = K["cim"].bounds
        ax.text((cb_[0] + cb_[2]) / 2 + 3, (cb_[1] + cb_[3]) / 2, "ÇİM / ETKİNLİK ALANI", ha="center",
                va="center", fontsize=5.5, color="#3f6212", zorder=7)
        sb_ = K["serit"].bounds
        ax.text((sb_[0] + sb_[2]) / 2, (sb_[1] + sb_[3]) / 2, "ACİL DURUM VE YAYA YOLU (3,5 m, çim taşı)",
                ha="center", va="center", fontsize=5, color="#44403c", zorder=7)
        db_ = K["donus"].bounds
        ax.text((db_[0] + db_[2]) / 2, (db_[1] + db_[3]) / 2 - 1.2, "DÖNÜŞ\nMEYDANI", ha="center", va="center",
                fontsize=5, color="#44403c", zorder=7)
        ax.text((K["cop"].bounds[0] + K["cop"].bounds[2]) / 2, K["cop"].bounds[1] - 0.6, "çöp · bisiklet",
                ha="center", va="top", fontsize=4.5, color="#44403c", zorder=7)
    for mp in MISAFIR:
        draw_poly(ax, mp, facecolor="#cbd5e1", edgecolor="#64748b", lw=0.4, zorder=3)
        c_ = mp.centroid
        ax.text(c_.x, c_.y, "M", ha="center", va="center", fontsize=4.5, color="#334155", zorder=6)
    for a in ARALAR:                       # bloklar arası mesafe ölçüsü
        if a.get("meydan"):
            continue
        vv = (ust[0] + ust[1]) / 2 if a["sira"] == "A" else (alt[0] + alt[1]) / 2
        ax.annotate("", (a["u0"], vv), (a["u1"], vv), arrowprops=dict(arrowstyle="<->", lw=0.6, color="#b91c1c"),
                    zorder=9)
        ax.text((a["u0"] + a["u1"]) / 2, vv + 0.6, f"{BLOK_ARA:.2f}".replace(".", ","), ha="center",
                fontsize=6, color="#b91c1c", zorder=9)
    for m in MAH:   # balkon yan duvarları zemindeki teras duvarıyla aynı izde, ayrıca çizilmez
        if m["tip"] != "balkon":
            draw_poly(ax, m["poly"], facecolor=C["mah"], edgecolor="none", zorder=6)
    for v in villas:
        for bk in ("balkon", "balkon_on"):
            bx = list(v[bk].exterior.coords)
            ax.plot([p[0] for p in bx], [p[1] for p in bx], ls=(0, (2, 1.5)), lw=0.5, color=C["ev"], zorder=5)
        c = v["ev"].centroid
        ax.text(c.x, c.y, f"V{v['no']}", ha="center", va="center", fontsize=6.2,
                fontweight="bold", color=C["yazi"], rotation=90, zorder=6)
        for pp in v["parklar"]:
            pc = pp.centroid
            ax.text(pc.x, pc.y, "P", ha="center", va="center", fontsize=4.5, color="white", zorder=6)
    draw_poly(ax, YOL_POLY, facecolor=C["yol"], edgecolor="#78716c", lw=0.5, zorder=2)
    ym = (yol[0] + yol[1]) / 2
    ax.plot([PARSEL.bounds[0], PARSEL.bounds[2]], [ym, ym], ls=(0, (6, 4)), lw=0.5, color="white", zorder=3)
    ax.text((PARK["lot0"] + X_ALT + L_ALT) / 2 if PARK else X_ALT + L_ALT * (0.25 if MEYDAN else 0.5), ym,
            "OTOPARK YOLU (6 m)" if PARK else f"SİTE İÇİ YOL  ({YOL:.0f} m)", ha="center", va="center", fontsize=7,
            color="#44403c", zorder=6, bbox=dict(fc=C["yol"], ec="none", pad=0.6))

    # parsel ve çekme hattı
    px, py = PARSEL.exterior.xy
    ax.plot(px, py, color=C["parsel"], lw=1.6, zorder=8)
    sx, sy = SETBACK_LINE.xy
    ax.plot(sx, sy, color=C["cekme"], lw=0.6, ls=(0, (5, 2, 1, 2)), zorder=7)
    cen = PARSEL.centroid
    pts = list(PARSEL.exterior.coords)
    for a, b in zip(pts[:-1], pts[1:]):
        L = math.dist(a, b)
        tt = 0.5
        if yol[0] - 3 < (a[1] + b[1]) / 2 < yol[1] + 3:     # yol ağzındaki kenar: ölçüyü kaydır
            tt = 0.8 if a[1] < b[1] else 0.2
        mx_, my_ = a[0] + (b[0] - a[0]) * tt, a[1] + (b[1] - a[1]) * tt
        nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L     # sola normal
        if (mx_ + nx - cen.x) ** 2 + (my_ + ny - cen.y) ** 2 < (mx_ - cen.x) ** 2 + (my_ - cen.y) ** 2:
            nx, ny = -nx, -ny
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        if ang > 90: ang -= 180
        if ang < -90: ang += 180
        ax.text(mx_ + nx * 2.0, my_ + ny * 2.0, f"{L:.2f}", fontsize=5.5, color=C["parsel"],
                ha="center", va="center", rotation=ang, zorder=9)

    # ölçü: tipik villa
    v = villas[N_UST // 2]
    e = v["ev"].bounds
    ax.annotate("", (e[0], e[3] + 6.2), (e[2], e[3] + 6.2),
                arrowprops=dict(arrowstyle="<->", lw=0.5, color="#374151"))
    ax.text((e[0] + e[2]) / 2, e[3] + 6.9, f"{W:.2f}", fontsize=5.5, ha="center", color="#374151")

    # sıra etiketleri, giriş notları
    ax.text(X_UST + L_UST / 2, PARSEL.bounds[3] + 2.5, f"A SIRASI · {N_UST} VİLLA · arka bahçeler",
            fontsize=6.5, ha="center", color="#166534", zorder=9)
    ax.text(X_ALT + L_ALT * (0.25 if MEYDAN else 0.5), alt[0] - BALKON - 1.6, f"B SIRASI · {N_ALT} VİLLA · arka bahçeler",
            fontsize=6.5, ha="center", color="#166534", zorder=9)
    gx1 = YOL_POLY.bounds[2]
    ax.annotate("SİTE GİRİŞİ", (gx1 - 1.0, ym), (gx1 + 9.5, ym), fontsize=7.5, color="#b91c1c",
                fontweight="bold", ha="left", va="center",
                arrowprops=dict(arrowstyle="-|>", color="#b91c1c", lw=1.4), zorder=10)
    if CEP:
        cc = CEP_POLY.centroid
        ax.text(cc.x + 1.0, (alt_otp[0] + alt_otp[1]) / 2, "DÖNÜŞ\nCEBİ", fontsize=6, ha="center",
                va="center", color="#44403c", zorder=6)

    # kuzey oku (yerel çerçevede kuzey yönü)
    a = math.radians(EKSEN_ACI)
    nxv, nyv = math.sin(a), math.cos(a)
    kx, ky = x1 - 2, y1 + 1
    ax.add_patch(FancyArrow(kx - nxv * 4, ky - nyv * 4, nxv * 8, nyv * 8, width=0.6,
                            head_width=2.4, head_length=2.6, color="#111827", zorder=10,
                            length_includes_head=True))
    ax.text(kx + nxv * 6.5, ky + nyv * 6.5, "K", fontsize=10, fontweight="bold",
            ha="center", va="center")

    # ölçek çubuğu
    sx0, sy0 = x0, y0 - 4.5
    for i in range(5):
        ax.add_patch(MPoly([(sx0 + i * 5, sy0), (sx0 + i * 5 + 5, sy0), (sx0 + i * 5 + 5, sy0 + 0.8),
                            (sx0 + i * 5, sy0 + 0.8)], fc="#111827" if i % 2 == 0 else "white",
                           ec="#111827", lw=0.4))
    for m in (0, 10, 25):
        ax.text(sx0 + m, sy0 - 1.6, f"{m} m", fontsize=5.5, ha="center")

    # başlık ve tablo
    fig.text(20 / 420, 1 - 9 / 297, (f"VAZİYET PLANI (ÖN ÇALIŞMA): {len(villas)} İKİZ VİLLA, {len(BLOK_UST) + len(BLOK_ALT)} BLOK · VARYANT {VARYANT}"
              if ARALAR and set(BLOK_UST + BLOK_ALT) == {2} else
              f"VAZİYET PLANI (ÖN ÇALIŞMA): {len(villas)} VİLLA, {len(BLOK_UST) + len(BLOK_ALT)} BLOK · VARYANT {VARYANT}"
              if ARALAR else f"VAZİYET PLANI (ÖN ÇALIŞMA): {len(villas)} BİTİŞİK VİLLA · VARYANT {VARYANT}"), fontsize=15,
             fontweight="bold", color="#111827")
    fig.text(20 / 420, 1 - 14.5 / 297,
             f"{kml_data('İl')} / {kml_data('İlçe')} / {kml_data('Mahalle')} Mah. · "
             f"{kml_data('Ada')} Ada {PARSEL_NO} Parseller (tevhit) · Mevkii: {kml_data('Mevkii')} · "
             f"Pafta: {kml_data('Pafta')} · Varyant {VARYANT}: {VARYANT_ACIKLAMA}",
             fontsize=8.5, color="#374151")
    tx, ty = 20 / 420, 1 - (18 + ax_h * 297 + 10) / 297
    fig.text(tx, ty, "ALAN ÖZETİ", fontsize=9, fontweight="bold")
    for i, (k, val) in enumerate(ozet):
        yy = ty - (5 + i * 4.3) / 297
        fig.text(tx, yy, k, fontsize=7.2, color="#374151")
        fig.text(tx + 48 / 420, yy, val, fontsize=7.2, color="#111827")
    # lejant
    lx = 175 / 420
    fig.text(lx, ty, "LEJANT", fontsize=9, fontweight="bold")
    items = [(C["ev_fill"], C["ev"], "Villa (taban oturumu), kesikli: 1. kat ön ve arka balkon"),
             (C["park"], "#78716c", "Otopark (villa önü, 2,6 × 5,0 m)"),
             (C["otopark"], "#a8a29e", "Villa ön bahçesi / araç girişi"),
             (C["yol"], "#78716c", "Site içi yol"),
             (C["bahce"], "#86efac", "Villa özel bahçesi"),
             (C["ortak"], "none", "Ortak yeşil / artık alan"),
             ("#cbd5e1", "#64748b", "Misafir otoparkı (M)"),
             ] + ([("#c7e9b4", "#4d7c0f", "Sosyal meydan: havuz, deck, oyun alanı, pergola")] if MEYDAN else []) + \
        ([("#c7e9b4", "#4d7c0f", "Araçsız lineer park: oyun, pergola, hobi bahçesi, çim")] if PARK else []) + [
             (C["mah"], C["mah"], "Mahremiyet duvarı (h: teras {}, bahçe {}, giriş {} m) + 1. kat balkon yan duvarı"
              .format(*(f"{h:.1f}".replace(".", ",") for h in (MAH_H_TERAS, MAH_H_BAHCE, MAH_H_ON))))]
    for i, (fc, ec, lab) in enumerate(items):
        yy = ty - (5 + i * 4.3) / 297
        fig.patches.append(matplotlib.patches.Rectangle((lx, yy - 0.3 / 297), 6 / 420, 2.6 / 297,
                           transform=fig.transFigure, fc=fc, ec=ec, lw=0.5))
        fig.text(lx + 8 / 420, yy, lab, fontsize=7.2, color="#374151")
    yy = ty - (5 + len(items) * 4.3) / 297
    fig.lines.append(matplotlib.lines.Line2D([lx, lx + 6 / 420], [yy + 1 / 297] * 2, transform=fig.transFigure,
                                             color=C["cekme"], lw=0.8, ls=(0, (5, 2, 1, 2))))
    fig.text(lx + 8 / 420, yy, f"Yapı yaklaşma sınırı ({CEKME:.0f} m, varsayım)", fontsize=7.2, color="#374151")
    yy -= 4.3 / 297
    fig.lines.append(matplotlib.lines.Line2D([lx, lx + 6 / 420], [yy + 1 / 297] * 2, transform=fig.transFigure,
                                             color=C["parsel"], lw=1.6))
    fig.text(lx + 8 / 420, yy, "Parsel sınırı (TKGM), kenar uzunlukları metre", fontsize=7.2, color="#374151")
    # notlar
    nx_ = 290 / 420
    fig.text(nx_, ty, "NOTLAR", fontsize=9, fontweight="bold")
    notes = [
        "1. Ön çalışmadır; imar durumu (emsal, TAKS, kat adedi, çekme",
        "    mesafeleri, blok boyu) belediyeden alınıp teyit edilmelidir.",
        "2. Sınır TKGM KML'lerinden alınmış, 1 ve 2 parseller birleştirilmiştir.",
        f"    Koordinat yuvarlaması: çizim {geo_alan:,.0f} m², tapu {tapu_alan:,.0f} m².",
        "3. Site girişi sağ (kuzeydoğu) uçtan; yol sol uçta çıkmaz.",
        ("    Sol uçta 16 m × 6 m dönüş cebi bırakılmıştır." if CEP else
         "    Otopark yolunun ucunda 11 m × 7 m dönüş meydanı var." if PARK else
         "    Dönüş cebi YOK: itfaiye erişimi için uygun değildir."),
        ("4. İkiz villalar: her villanın ön, arka ve yan cephesi açık; bloklar" if OPS.get("iki_park") else
         "4. İç kısım araçsız: otopark girişte toplu; parktaki 3,5 m şerit" if PARK else
         "4. Ortadaki meydan iki yakayı yükseltilmiş geçitle bağlar; havuz" if MEYDAN else
         f"4. Bloklar arası {BLOK_ARA:.0f} m: önde 2 misafir otoparkı, arkada" if ARALAR else
         f"4. Villalar kesintisiz iki blok ({N_UST}+{N_ALT}); misafir otoparkı"),
        ("    arası 6 m yan bahçe (ortada 1,9 m duvar). Kat planı 8 × 9 m'ye uyarlanmalı." if OPS.get("iki_park") else
         "    itfaiye/ambulans/taşınma için açık (babalı). 1,5 m kademe." if PARK else
         "    çevresinde 1,2 m güvenlik çiti. Villalar ikişerli 1,5 m kademeli." if MEYDAN else
         "    uç villaların yan bahçeleri (ortada mahremiyet duvarı)." if ARALAR else
         "    ve ortak alan için yer kalmıyor."),
        "5. Ölçek 1/400 (A3). DXF dosyası TM30 / ITRF96 koordinatlıdır.",
    ]
    for i, n in enumerate(notes):
        fig.text(nx_, ty - (5 + i * 4.3) / 297, n, fontsize=6.8, color="#374151")
    fig.text(1 - 20 / 420, 8 / 297, "Ölçek 1/400 · A3", fontsize=7, ha="right", color="#6b7280")

    fig.savefig(path_pdf)
    fig.savefig(path_png, dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------- DXF (TM30 dünya koordinatı)
def write_dxf(path):
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.M
    msp = doc.modelspace()
    layers = {"PARSEL": 7, "CEKME": 1, "YOL": 8, "OTOPARK": 9, "PARK_YERI": 252, "VILLA": 30,
              "BALKON": 30, "BAHCE": 3, "ORTAK_ALAN": 82, "YAZI": 7, "MAHREMIYET_DUVARI": 251,
              "MAHREMIYET_BALKON": 251, "MISAFIR_OTOPARK": 5}
    for n, col in layers.items():
        doc.layers.add(n, color=col)
    doc.layers.get("CEKME").dxf.linetype = "DASHDOT"
    doc.layers.get("BALKON").dxf.linetype = "DASHED"
    doc.layers.get("MAHREMIYET_BALKON").dxf.linetype = "DASHED"

    def poly(g, layer):
        for p in getattr(g, "geoms", [g]):
            if p.geom_type == "Polygon" and not p.is_empty:
                msp.add_lwpolyline([to_world(*c) for c in p.exterior.coords[:-1]], close=True,
                                   dxfattribs={"layer": layer})

    poly(PARSEL, "PARSEL")
    poly(BUILD, "CEKME")
    poly(YOL_POLY, "YOL")
    poly(ORTAK, "ORTAK_ALAN")
    for m in MAH:
        poly(m["poly"], "MAHREMIYET_BALKON" if m["tip"] == "balkon" else "MAHREMIYET_DUVARI")
    for mp in MISAFIR:
        poly(mp, "MISAFIR_OTOPARK")
    for v in villas:
        poly(v["ev"], "VILLA")
        poly(v["balkon"], "BALKON")
        poly(v["balkon_on"], "BALKON")
        poly(v["otopark"], "OTOPARK")
        poly(v["park"], "PARK_YERI")
        poly(v["bahce"], "BAHCE")
        c = v["ev"].centroid
        msp.add_text(f"V{v['no']}", height=1.2, rotation=EKSEN_ACI + 90,
                     dxfattribs={"layer": "YAZI"}).set_placement(
            to_world(c.x, c.y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    c = PARSEL.centroid
    msp.add_text(f"{kml_data('Ada')} ADA {PARSEL_NO} PARSEL", height=2.0,
                 rotation=EKSEN_ACI, dxfattribs={"layer": "YAZI"}).set_placement(
        to_world(c.x, PARSEL.bounds[1] - 5), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    doc.saveas(path)


if __name__ == "__main__":
    if len(sys.argv) == 1:      # varsayılan: her iki varyantı ayrı süreçte üret
        import subprocess
        for k in VARYANTLAR:
            subprocess.run([sys.executable, __file__, k], check=True)
        raise SystemExit
    ad = f"vaziyet_169-1-2_{VARYANT}"
    render(ad + ".pdf", ad + ".png")
    write_dxf(ad + ".dxf")
    print(f"--- Varyant {VARYANT}: W={W:.2f} D={D:.2f} üst arka={UST_ARKA} A x0={X_UST} B x0={X_ALT}")
    for k, v in ozet:
        print(f"{k:24s} {v}")
