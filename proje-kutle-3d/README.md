# Proje Kütlesi: 3B Model ve Render

Odunluk Caddesi'ndeki zemin kat dükkan + 7 normal katlı konut projesinin, AutoCAD'den basılmış PDF planlardan otomatik çıkarılan 3B kütle modeli.

| Kat | Kullanım | Kat yüksekliği | Kot |
|---|---|---|---|
| Zemin | 4 dükkan + önlerinde örtülü teras | 4,50 m | ±0,00 → +4,50 |
| 1.–7. | Her katta 4 daire, 5 balkon | 7 × 3,30 m | +4,50 → +27,60 |
| Çatı | Parapet (varsayım) | 1,00 m | +28,60 |
| Çatı | Merdiven/asansör kulesi (varsayım) | 3,00 m | +30,60 |

Planlardan ölçülen değerler (yaklaşık):

- Parsel: ~2.990 m², Odunluk Caddesi cephesi ~32 m, derinlik ~100 m
- Zemin kat oturumu: ~790 m² (kapalı ~675 m² + 4 teras)
- Normal kat döşemesi: ~455 m² (kapalı ~414 m² + balkonlar)
- 55 açık otopark yeri (planlardaki yerlerin tamamı)

## Çıktılar (`cikti/`)

| Dosya | İçerik |
|---|---|
| `01_cadde_kusbakisi.png` | Odunluk Caddesi tarafından kuş bakışı |
| `02_otopark_kusbakisi.png` | Otopark tarafından kuş bakışı |
| `03_cadde_goz_hizasi.png` | Karşı kaldırımdan göz hizası |
| `04_kil_kutle.png` | Beyaz kil kütle (çevre gri) |
| `05_vaziyet_ustten.png` | Üstten vaziyet görünüşü, parsel sınırı işaretli |
| `06_gorunus_kotlar.png` | Güney görünüşü, kat kotları ve toplam yükseklik |
| `proje_kutle.blend` | Blender sahnesi (kameralar, ışık, malzemeler dahil) |
| `proje_kutle.glb` | glTF: web, SketchUp (eklentiyle), Rhino, 3ds Max, Unreal/Unity |
| `proje_kutle.obj` + `.mtl` | OBJ: hemen her 3B yazılım |
| `proje_kutle.dae` | Collada: SketchUp'ta *Dosya → İçe Aktar* ile doğrudan açılır |

Birim metredir. Orijin zemin kat binasının ortasıdır; +X caddeye, +Y Otel bölgesine bakar.

## Gerçekçi render'lar (`cikti_gercekci/`)

`gercekci_render.py` binayı içi dolu bir kütle yerine **plandaki gerçek duvarlarla** kurar:

- Dış duvarlar ve iç bölmeler normal kat ve zemin kat planlarından gelir; pencere ve balkon kapısı boşlukları plandaki yerlerinde duvarı keser. Pencerelerden odalar, perdeler, dükkan içleri ve tavan ışıkları görünür.
- Doğramalar (antrasit), kayıtlar, dış denizlikler, cam korkuluklu balkonlar, döşeme bantları, parapet harpuştaları, çatıda merdiven/asansör kulesi ve klima üniteleri.
- Zemin katta vitrinler, saçak altı spotları, teraslarda masa-sandalye ve saksılar; gezilemeyen terasta çakıl.
- Çevre: Poly Haven (CC0) bulutlu gökyüzü HDRI'ı, sıva, asfalt, beton parke, çim ve çakıl dokuları, zeytin ağaçları, sokak lambaları; otoparkta ve caddede araçlar, yaya geçidi ve yol çizgileri.
- Akşam görünümünde daireler rastgele aydınlık, dükkanlar ve sokak lambaları yanık.

| Dosya | Görünüm |
|---|---|
| `01_cadde_kusbakisi.png` | Odunluk Caddesi tarafından kuş bakışı |
| `02_otopark_kusbakisi.png` | Otopark tarafından kuş bakışı |
| `03_cadde_goz_hizasi.png` | Karşı kaldırımdan göz hizası |
| `04_dukkan_teraslari.png` | Dükkan terasları ve saçak altı |
| `05_kuzeydogu_kusbakisi.png` | Kuzeydoğudan kuş bakışı |
| `06_aksam_goz_hizasi.png` | Akşam, göz hizası |
| `07_aksam_kusbakisi.png` | Akşam, kuş bakışı |

```bash
python varliklar_indir.py                      # Poly Haven'dan HDRI, doku ve modeller (~260 MB, bir kez)
python gercekci_render.py --out cikti_gercekci # 7 görünüm, 4 çekirdek CPU'da ~1 saat
python gercekci_render.py --out deneme --scale 0.4 --samples 24 --only goz,aksam   # hızlı deneme
```

Cephe malzemeleri (beyaz sıva, balkon içlerinde terrakota kaplama, antrasit zemin kat paneli), doğrama rengi, perdeler, mobilya, araçlar, ağaçlar ve çevre binaları **temsilidir**; projede tanımlı değildir. Çevre binaları gerçek komşu yapıları göstermez.

## Yöntem

1. **`plan_cikar.py`**: PDF'lerdeki vektör çizgileri okur.
   - Kalın kırmızı duvar katmanı poligonlara dönüştürülür; oda adları ve alan etiketleri poligonlara atanır.
   - **Ölçek**, AutoCAD'in yazdığı 26 oda alanıyla (ör. *Oda Alan:10.67m²*) poligon alanları karşılaştırılarak bulunur: 1 pt = 3,296 cm (baskı ~1/93). Bu ölçekle otopark yerleri tam 2,50 × 5,00 m çıkar.
   - Zemin kat PDF'i normal kattan %1,45 daha büyük ölçekle basılmış. İki plan, ikisinde de çizili 46 otopark yeri üzerinden ölçek + kaydırma ile eşleştirilir. Asansör kuyuları da sonuçta üst üste oturur (sapma < 1 cm).
   - Balkonlar, giriş boşluğu, merdiven/asansör çekirdeği, dükkan terasları ve "gezilemeyen teras" etiketlerden ayrılır. Pencereler (camgöbeği katman) ve balkon kapıları cepheye yerleştirilir.
   - Sonuç `plan_geometri.json` dosyasına metre cinsinden yazılır.
2. **`kutle_blender.py`**: JSON'dan sade kütle sahnesini kurar (Cycles render), görünüşe kotları işler ve modeli dışa aktarır.
3. **`gercekci_render.py`**: Aynı JSON'daki duvar, oda ve açıklıklarla detaylı binayı kurar ve gerçekçi render alır.

## Yeniden üretme

```bash
pip install pymupdf shapely opencv-python-headless pillow trimesh pycollada
pip install bpy            # Blender 5.x Python modülü (Python 3.13 gerekir)

python plan_cikar.py --zemin zemin_kat.pdf --normal normal_kat.pdf --out plan_geometri.json --debug kontrol.png
python kutle_blender.py --json plan_geometri.json --out cikti            # ~10 dk, 4 çekirdek CPU
python kutle_blender.py --json plan_geometri.json --out deneme --scale 0.5 --samples 16 --no-export   # hızlı deneme
```

Kat yüksekliği ve kat sayısı `kutle_blender.py` başındaki `ZEMIN_H`, `KAT_H`, `KAT_SAYISI` sabitleriyle değişir. `--no-kule` çatıdaki merdiven/asansör kulesini kaldırır. `--only cadde,kil` yalnızca seçili görünümleri render eder.

## Varsayımlar

- Planlarda kuzey oku yok; güneş yönü görsellik için seçilmiştir, gölgeler gerçek yönelimi göstermez.
- Çatı planı verilmediği için çatı düz kabul edildi. 1,00 m parapet ve 3,00 m merdiven/asansör kulesi varsayımdır.
- Zemin kat planında pencere çizilmediği için dükkan cepheleri ~3 m'lik vitrin camlarıyla modellendi. Teraslar, üstteki gezilemeyen teras döşemesinin altında örtülü kabul edildi.
- İki kanat arasındaki giriş boşluğu (zemin katta *Bina Girişi*) normal katlarda da cepheye açık bir boşluk olarak modellendi.
- Normal kat pencere/kapı boyları: pencere denizliği 0,90 m, üst kotu 2,45 m; balkon kapıları 0 – 2,45 m.
- Bodrum (kapalı otopark) planı verilmediği için modellenmedi.
- Bu bir kütle çalışmasıdır: cephe malzemeleri, doğramalar ve çevre (ağaçlar, araçlar, yol) temsilidir.
