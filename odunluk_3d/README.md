# 4622/3 – Odunluk Caddesi · 3D model ve render

Kat planı PDF'lerinden (zemin, 1–6. kat, 7. kat) vektörel olarak ölçü okunup Blender/Cycles ile
parametrik olarak kurulan 3D model ve renderlar.

## Klasör

| Dosya | İçerik |
|---|---|
| `renders/` | Final renderlar (JPG) |
| `model/odunluk_4622_3.blend` | Blender 5.x sahnesi (ana blok + ticari blok + vaziyet; çevre kütleleri/ağaçlar hariç). Zemin dokuları ve HDRI dosyaya gömülü değildir; `download_assets.py` ile indirilir |
| `model/odunluk_4622_3.glb` | Aynı modelin dokusuz glTF hali (herhangi bir 3D görüntüleyicide açılır) |
| `build.py` | Modeli kuran ve render alan betik |
| `download_assets.py` | Gökyüzü HDRI, zemin dokuları ve ağaç modellerini (Poly Haven, CC0) indirir |

## Plandan okunan ölçüler

PDF'ler A0'a sığdırılarak basılmış; dükkan alanları (83,6 / 85,4 / 78,5 / 33 / 32,8 m²) ile
çizim karşılaştırılarak gerçek ölçek ≈ 1:96,6 bulundu ve tüm ölçüler buna göre düzeltildi.

| | |
|---|---|
| Ana blok (cadde cepheli) | 27,67 × 23,38 m, batıya açık U plan (avlu 12,9 × 10,6 m) |
| Kat adedi | Zemin (dükkan) + 6 normal kat + 7. kat (yalnız doğu yarısı; batısı gezilemeyen teras) |
| Kat yüksekliği | 2,95 m (plandaki merdiven notu: 18 rıht × 16,38 cm) – zemin kat dahil |
| Balkonlar | Doğu cephede 3, batı kanat uçlarında 2 adet, 1,63 m derinlikte loggia |
| Ticari blok | 14,48 × 23,72 m, tek katlı, doğuya açık C plan |
| Parsel | ≈ 105 × 33 m; batıda 29 araçlık açık otopark, cadde önünde 9 araçlık otopark |

## Cephe (mekanik giydirme)

- **Fildişi porselen seramik** (120×60 cm, 12 mm derz) – ana gövde
- **Antrasit seramik** (60×120 cm) – cadde cephesindeki orta düşey bant ve zemin kat ayakları
- **Antrasit alüminyum kompozit** – 7. kat (taç), pencere aksı düşey şeritleri, tabela bandı, saçak, harpuşta
- **Ahşap görünümlü seramik** – balkon arka duvarları
- Cam korkuluk, antrasit doğrama

## Varsayımlar (planda bilgi olmayan yerler)

- Kesit olmadığı için zemin kat yüksekliği de 2,95 m alındı (`--gf 4.5` gibi bir değerle değiştirilebilir).
- Zemin planında ticari blok kolları 14,99 m, üst kat planlarında 17,13 m çiziliydi; alanları tutan zemin planı esas alındı.
- Kapalı otopark girişi güneydoğuda ok ile gösterildiği için güney sınır boyunca bir rampa modellendi.
- Çevre yapılar, güneydeki park, ağaçlar ve araçlar temsilidir.

## Yeniden üretmek

```bash
pip install bpy pillow
python3 download_assets.py assets
python3 build.py --assets assets --view hero --res 2700 1800 --samples 160 --out renders/hero.png
# görünümler: hero, north, court, west, aerial, detail
```
