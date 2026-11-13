"""
Gerçekçi render için Poly Haven'dan (CC0) HDRI, doku ve modelleri indirir.

    python varliklar_indir.py            # varliklar/ klasörüne

Klasör ~450 MB'tır ve depoya eklenmez (.gitignore).
"""

import json
import os
import sys
import urllib.request

UA = {"User-Agent": "kutle-render/1.0"}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "varliklar")

HDRI = {"kloofendal_48d_partly_cloudy_puresky": "4k",   # gündüz, parçalı bulutlu
        "evening_road_01_puresky": "4k"}                # akşam / gün batımı
TEXTURES = {
    "white_stucco": "2k",               # ana cephe sıvası
    "concrete_tile_facade": "2k",       # zemin kat antrasit panel
    "exterior_wall_cladding_02": "2k",  # balkon iç duvarı terrakota kaplama
    "asphalt_02": "2k",                 # otopark ve yol
    "concrete_pavers_02": "2k",         # kaldırım ve bina çevresi
    "aerial_grass_rock": "2k",          # parsel dışı arazi
    "leafy_grass": "1k",                # yeşil şeritler
    "gravel_floor": "1k",               # gezilemeyen teras ve çatı çakılı
}
MAPS = ("Diffuse", "nor_gl", "Rough", "Displacement")
MODELS = {
    "island_tree_01": "1k",
    "island_tree_02": "1k",
    "street_lamp_01": "1k",
    "outdoor_table_chair_set_01": "1k",
    "planter_box_01": "1k",
}


def api(path):
    return json.load(urllib.request.urlopen(urllib.request.Request("https://api.polyhaven.com/" + path, headers=UA), timeout=60))


def fetch(url, dst):
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + ".part"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r, open(tmp, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    os.replace(tmp, dst)
    print("  ", os.path.relpath(dst, OUT), f"{os.path.getsize(dst) / 1e6:.1f} MB", flush=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, res in HDRI.items():
        f = api("files/" + name)
        fetch(f["hdri"][res]["hdr"]["url"], os.path.join(OUT, "hdri", f"{name}_{res}.hdr"))
    for name, res in TEXTURES.items():
        f = api("files/" + name)
        for m in MAPS:
            if m in f and res in f[m]:
                fmt = "jpg" if "jpg" in f[m][res] else next(iter(f[m][res]))
                fetch(f[m][res][fmt]["url"], os.path.join(OUT, "doku", name, f"{m}.{fmt}"))
    for name, res in MODELS.items():
        b = api("files/" + name)["blend"][res]["blend"]
        base = os.path.join(OUT, "model", name)
        fetch(b["url"], os.path.join(base, f"{name}_{res}.blend"))
        for rel, inc in b.get("include", {}).items():
            fetch(inc["url"], os.path.join(base, rel))
    print("Tamam:", OUT)


if __name__ == "__main__":
    sys.exit(main())
