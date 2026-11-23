"""Poly Haven (CC0) dokularini, modellerini ve HDRI dosyasini assets/ klasorune indirir.

Kullanim: python indir.py assets
"""
import json, os, sys, urllib.request, concurrent.futures as cf
OUT = sys.argv[1]
TEX = {'plastered_wall_02': '2k', 'clay_roof_tiles_02': '2k', 'rectangular_facade_tiles_02': '2k', 'granite_tile_04': '2k',
       'concrete_pavers_02': '2k', 'rectangular_paving': '2k', 'asphalt_02': '2k', 'leafy_grass': '2k', 'concrete_tile_facade': '2k', 'exterior_wall_cladding_03': '2k'}
MODELS = {'jacaranda_tree': '1k', 'island_tree_01': '1k', 'island_tree_02': '1k', 'shrub_02': '1k', 'searsia_lucida': '1k', 'shrub_03': '1k'}
HDRI = ('kloofendal_48d_partly_cloudy_puresky', '4k')
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'asset-fetch'}), timeout=120) as r:
        return r.read()
def save(url, path):
    if os.path.exists(path): return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = get(url); open(path, 'wb').write(data); return path
jobs = []
for t, res in TEX.items():
    f = json.loads(get(f'https://api.polyhaven.com/files/{t}'))
    for m in ('Diffuse', 'nor_gl', 'Rough', 'Displacement'):
        if m in f and res in f[m]:
            jobs.append((f[m][res]['jpg']['url'], f'{OUT}/tex/{t}/{m}.jpg'))
for mdl, res in MODELS.items():
    f = json.loads(get(f'https://api.polyhaven.com/files/{mdl}'))
    g = f['gltf'][res]['gltf']
    jobs.append((g['url'], f'{OUT}/models/{mdl}/{mdl}.gltf'))
    for p, inc in g.get('include', {}).items():
        jobs.append((inc['url'], f'{OUT}/models/{mdl}/{p}'))
f = json.loads(get(f'https://api.polyhaven.com/files/{HDRI[0]}'))
jobs.append((f['hdri'][HDRI[1]]['hdr']['url'], f'{OUT}/hdri/{HDRI[0]}.hdr'))
with cf.ThreadPoolExecutor(8) as ex:
    for p in ex.map(lambda j: save(*j), jobs): pass
print(len(jobs), 'dosya')
