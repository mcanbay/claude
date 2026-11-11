"""Ürün fotoğrafının beyaz stüdyo arka planını kenarlardan flood-fill ile temizler.
Çıktı: public/cup.png (şeffaf), public/badge.png (kapaktaki '20g PROTEIN' rozeti yakın plan)."""
import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

src, out_dir = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB")
a = np.asarray(im).astype(np.int16)
# beyaza yakın pikseller
whiteish = (a.min(axis=2) > 228) & ((a.max(axis=2) - a.min(axis=2)) < 22)
lab, _ = ndimage.label(whiteish)
edge_labels = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
bg = np.isin(lab, list(edge_labels))
# küçük delikleri kapat, kenarı hafif yumuşat
fg = ~bg
fg = ndimage.binary_opening(fg, iterations=2)
fg = ndimage.binary_fill_holes(fg)
alpha = Image.fromarray((fg * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
rgba = im.copy(); rgba.putalpha(alpha)
bbox = alpha.getbbox()
cup = rgba.crop(bbox)
cup.save(f"{out_dir}/cup.png", optimize=True)
print("cup", cup.size)
# '20g PROTEIN' rozeti (kapak üzerindeki)
badge = im.crop((985, 740, 1320, 935))
badge.save(f"{out_dir}/badge.png")
print("badge", badge.size)
