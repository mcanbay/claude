"""sablon.html + units.json -> index.html (Artifact sürümü) ve model.html (tek başına açılan sürüm).

Kullanım: python build.py
"""
import json, pathlib
here = pathlib.Path(__file__).parent
units = (here / 'units.json').read_text(encoding='utf-8')
json.loads(units)  # doğrulama
ring = (here / 'ring.json').read_text(encoding='utf-8')
json.loads(ring)
body = (here / 'sablon.html').read_text(encoding='utf-8').replace('/*UNITS*/null', units).replace('/*RING*/null', ring)
root = here.parent
(root / 'index.html').write_text(body, encoding='utf-8')
standalone = ('<!doctype html>\n<html lang="tr">\n<head>\n<meta charset="utf-8">\n'
              '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
              '<style>body{margin:0;font:14px system-ui,sans-serif}</style>\n</head>\n<body>\n'
              + body + '\n</body>\n</html>\n')
(root / 'model.html').write_text(standalone, encoding='utf-8')
print('index.html', len(body), 'bayt; model.html', len(standalone), 'bayt')
