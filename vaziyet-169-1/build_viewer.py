# -*- coding: utf-8 -*-
"""3B görüntüleyici sayfasını üretir.

Kullanım: python build_viewer.py [B] [--three <three.js taban yolu>] [--out dosya] [--artifact]
  varsayılan:  model GLB sayfaya gömülür, tek başına açılabilen tam HTML dosyası yazılır
  --artifact:  model gömülmez, sayfa yanındaki model-glb.txt (base64) dosyasını okur (yayın için)
"""
import base64, json, sys

args = [a for a in sys.argv[1:] if not a.startswith("--")]
var = args[0] if args else "B"
three = "https://cdn.jsdelivr.net/npm/three@0.160.0"
if "--three" in sys.argv:
    three = sys.argv[sys.argv.index("--three") + 1]
out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else f"model_169-1-2_{var}.html"

meta = json.load(open(f"model_169-1-2_{var}.json", encoding="utf-8"))
artifact = "--artifact" in sys.argv
glb = "" if artifact else base64.b64encode(open(f"model_169-1-2_{var}.glb", "rb").read()).decode()
o = meta["ozet"]
tr = lambda x, d=2: f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
html = open("viewer_template.html", encoding="utf-8").read()
for k, v in {
    "__THREE__": three, "__META__": json.dumps(meta, ensure_ascii=False), "__GLB_B64__": glb,
    "__N__": str(o["n"]), "__BLOK__": o.get("blok", "16 / 16"), "__VAR__": var, "__W__": tr(o["W"]), "__D__": tr(o["D"]), "__BRUT__": f"{o['brut']:.0f}",
    "__TAPU__": tr(o["tapu"]), "__TAKS__": tr(o["taks"]), "__KAKS__": tr(o["kaks"]),
    "__UST__": tr(meta["ust"]), "__CATI__": tr(meta["cati"]),
}.items():
    html = html.replace(k, v)
if not artifact:
    html = ('<!doctype html>\n<html lang="tr">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<style>body{margin:0}</style>\n</head>\n<body>\n' + html + '\n</body>\n</html>\n')
open(out, "w", encoding="utf-8").write(html)
print(out, len(html) // 1024, "KB")
