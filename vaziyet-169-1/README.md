# 169 Ada 1 + 2 Parseller (tevhit): 32 Bitişik Villa Vaziyet Planı (ön çalışma)

Bursa / Nilüfer / İrfaniye Mah., Karaçalılık mevkii. 1 parsel (5.717,80 m²) ile 2 parsel (678,70 m²)
birleştirilerek tek parsel (6.396,50 m²) olarak çalışılmıştır.

| Dosya | İçerik |
|---|---|
| `vaziyet_169-1-2_A.pdf/.png/.dxf` | **Varyant A (önerilen):** 6,30 m cepheli villa, sol uçta 16 × 6 m dönüş cebi |
| `vaziyet_169-1-2_B.pdf/.png/.dxf` | **Varyant B:** 6,60 m cepheli villa, dönüş cebi yok |
| `vaziyet.py` | Planı üreten betik (parametreler dosyanın başında) |
| `model_169-1-2_B.glb` | Varyant B 3B kütle modeli (Blender, SketchUp, Windows 3B Görüntüleyici) |
| `model_169-1-2_B.html` | Modelin tarayıcıda açılan görüntüleyicisi (model içine gömülü; internet bağlantısı gerekir) |
| `render/` | Görüntüleyiciden alınmış render görselleri |
| `model3d.py`, `build_viewer.py`, `viewer_template.html` | 3B modeli ve görüntüleyiciyi üreten betikler |
| `parsel-169-1.kml`, `parsel-169-2.kml` | TKGM parsel sorgu çıktıları |

PDF dosyaları A3 yatay ve 1/400 ölçeklidir. DXF dosyaları TM30 / ITRF96 (EPSG:5254) koordinatlıdır ve katmanlara ayrılmıştır.

Yeniden üretmek için: `pip install shapely ezdxf pyproj matplotlib`, ardından `python vaziyet.py`
(iki varyantı da üretir) veya `python vaziyet.py A`.

Yerleşim: Site girişi sağ (kuzeydoğu) uçtan. Ortada 6 m site içi yol, iki yanda 16'şar bitişik villa.
Villa Z+1, 165 m² brüt (balkon dahil). Her villanın önünde 5 m'lik ön bahçede 1 otopark yeri var.
Betik, verilen villa sayısı için en geniş cepheyi ve iki sıranın bahçelerini dengeleyen yol konumunu kendisi bulur.

## 3B model (Varyant B)

`python model3d.py B` modeli üretir. Ardından `python build_viewer.py B` görüntüleyici sayfasını hazırlar
(`pip install trimesh mapbox_earcut scipy` gerekir).
Villalar zemin + 1 kattır. Kat yüksekliği 3,15 m, subasman 0,45 m. Saçak +6,75 m, mahya +8,40 m.
Çatı %30 eğimli beşik çatıdır ve mahyası sıra boyunca uzanır.
1. katta 1,5 m'lik arka balkon var. Model temsili bir kütle çalışmasıdır; cephe düzeni mimari projede netleşecek.

### Mahremiyet duvarları

Komşu villalar arasında, `vaziyet.py` içinde tanımlıdır (`MAH`). Aynı geometri 2B paftada, DXF'te ve 3B modelde kullanılır:

| Yer | Yükseklik | Boy |
|---|---|---|
| Arka bahçe, teras boyunca | 2,4 m | cepheden itibaren 3,5 m |
| Arka bahçe, teras sonrası | 1,9 m | bahçe sonuna (çevre duvarına) kadar |
| Ön bahçe, yan yana gelen iki giriş yolu arasında | 1,4 m | cepheden itibaren 4,0 m |
| 1. kat, balkonlar arasında | balkon döşemesinden saçağa kadar | 1,6 m (balkon derinliği + 0,1 m) |

Duvarlar 20 cm kalınlığındadır. DXF'te `MAHREMIYET_DUVARI` ve `MAHREMIYET_BALKON` katmanlarındadır.
