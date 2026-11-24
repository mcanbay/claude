# Satır yerleşimi optimizasyonu (yerel eksen: u = uzun eksen, v = enine)
import math, re, sys
from shapely.geometry import Polygon, box
from shapely import affinity
from pyproj import Transformer
txt=open('parsel-169-1.kml',encoding='utf-8').read()
c=re.search(r'<coordinates>(.*?)</coordinates>',txt,re.S).group(1).split()
ll=[tuple(map(float,s.split(',')[:2])) for s in c][:-1]
t=Transformer.from_crs(4326,5254,always_xy=True)
pts=[t.transform(*p) for p in ll]
ANG=69.6
P=Polygon(pts); ox,oy=P.centroid.x,P.centroid.y
L=affinity.rotate(affinity.translate(P,-ox,-oy),-ANG,origin=(0,0))
mx,my=L.bounds[:2]; L=affinity.translate(L,-mx,-my)
SB=3.0
B=L.buffer(-SB,join_style=2)
def fit_row(y0,y1,w,minx=0):
    # en uzun bitişik dizi: u ekseninde her w adımında kutu B içinde mi
    best=None
    xs=[i*0.1 for i in range(0,1200)]
    ok=[B.contains(box(x,y0,x+w,y1)) for x in xs]
    # first ok x then count consecutive
    start=next(i for i,o in enumerate(ok) if o)
    x=xs[start]; n=0
    while B.contains(box(x+n*w,y0,x+(n+1)*w,y1)): n+=1
    return x,n
D,PK,RD=float(sys.argv[1]),5.0,6.0
res=[]
for top10 in range(470,540,5):
    top=top10/10
    up=(top-D,top); road=(up[0]-PK-RD,up[0]-PK); lo=(road[0]-PK-D,road[0]-PK)
    for w100 in range(580,661,5):
        w=w100/100
        xu,nu=fit_row(*up,w); xl,nl=fit_row(*lo,w)
        res.append((nu+nl,w,top,nu,nl,round(xu,1),round(xl,1),round(lo[0],1)))
res=[r for r in res if r[0]>=32]
res.sort(key=lambda r:(-r[1],r[2]))
for r in res[:15]: print(r)
