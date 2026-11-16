import json, os, sys, urllib.request, subprocess
A=sys.argv[1]
def get(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path) and os.path.getsize(path)>0: return
    subprocess.run(['curl','-sS','-L','--retry','3','-m','600','-o',path,url],check=True)
def files(a):
    p=f'/tmp/f_{a}.json'
    if not os.path.exists(p): subprocess.run(['curl','-sS','-m','60','-o',p,f'https://api.polyhaven.com/files/{a}'],check=True)
    return json.load(open(p))
# models (blend 1k)
for a in ['island_tree_02','tree_small_02','shrub_03','jacaranda_tree']:
    f=files(a)['blend']['1k']['blend']
    d=f'{A}/models/{a}'
    get(f['url'], f'{d}/{a}.blend')
    for rel,inc in f.get('include',{}).items(): get(inc['url'], f'{d}/{rel}')
    print('model',a)
# textures 2k jpg
for a in ['asphalt_02','concrete_pavers','rectangular_paving','leafy_grass','concrete_pavement','asphalt_04']:
    f=files(a)
    for m,key in [('Diffuse','diff'),('nor_gl','nor'),('Rough','rough')]:
        if m in f and '2k' in f[m]:
            v=f[m]['2k'].get('jpg') or f[m]['2k'].get('png')
            get(v['url'], f'{A}/tex/{a}_{key}.jpg')
        else: print('  missing',a,m, [k for k in f.keys()])
    print('tex',a)
# hdri
for a in ['kloofendal_48d_partly_cloudy_puresky']:
    f=files(a)
    v=f['hdri']['4k']['hdr']
    get(v['url'], f'{A}/hdri/{a}_4k.hdr')
    print('hdri',a)
