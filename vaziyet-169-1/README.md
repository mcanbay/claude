# 169 Ada 1 + 2 Parseller (tevhit): 32 Bitişik Villa Vaziyet Planı (ön çalışma)

Bursa / Nilüfer / İrfaniye Mah., Karaçalılık mevkii. 1 parsel (5.717,80 m²) ile 2 parsel (678,70 m²)
birleştirilerek tek parsel (6.396,50 m²) olarak çalışılmıştır.

| Dosya | İçerik |
|---|---|
| `vaziyet_169-1-2_A.pdf/.png/.dxf` | **Varyant A (önerilen):** 6,30 m cepheli villa, sol uçta 16 × 6 m dönüş cebi |
| `vaziyet_169-1-2_B.pdf/.png/.dxf` | **Varyant B:** 6,60 m cepheli villa, dönüş cebi yok |
| `vaziyet.py` | Planı üreten betik (parametreler dosyanın başında) |
| `parsel-169-1.kml`, `parsel-169-2.kml` | TKGM parsel sorgu çıktıları |

PDF dosyaları A3 yatay ve 1/400 ölçeklidir. DXF dosyaları TM30 / ITRF96 (EPSG:5254) koordinatlıdır ve katmanlara ayrılmıştır.

Yeniden üretmek için: `pip install shapely ezdxf pyproj matplotlib`, ardından `python vaziyet.py`
(iki varyantı da üretir) veya `python vaziyet.py A`.

Yerleşim: Site girişi sağ (kuzeydoğu) uçtan. Ortada 6 m site içi yol, iki yanda 16'şar bitişik villa.
Villa Z+1, 165 m² brüt (balkon dahil). Her villanın önünde 5 m'lik ön bahçede 1 otopark yeri var.
Betik, verilen villa sayısı için en geniş cepheyi ve iki sıranın bahçelerini dengeleyen yol konumunu kendisi bulur.
