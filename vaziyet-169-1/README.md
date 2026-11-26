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
| `kat_plani_4+1.pdf/.png/.dxf` | Tip villa 4+1 zemin ve 1. kat planları, metraj tablosu (A2, 1/50) |
| `cephe_gorunusleri.pdf/.png/.dxf` | Ön, arka, yan cephe (1/50) ve A sırası ön cephesi (1/200), A1 |
| `cephe.py` | Cephe görünüşlerini üreten betik |
| `kat_plani.py` | Kat planlarını üreten betik (mahaller, kapılar, pencereler, mobilya) |
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
Villalar zemin + 1 kattır. Kat yüksekliği 3,15 m, subasman 0,45 m.
Çatı betonarme düz çatıdır (gezilmeyen teras): döşeme +6,75, ısı ve su yalıtımı ile çakıl koruma üstü +7,05,
60 cm parapet ve alüminyum harpuşta üstü +7,65 (binanın en yüksek noktası). Yangın duvarları parapet hizasında biter.
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

## Tip villa 4+1 kat planı

`python kat_plani.py` ile üretilir. Villa 6,60 × 11,00 m (aks), iç ölçü 6,35 × 10,50 m.

| Kat | Mahaller (net m²) |
|---|---|
| Zemin | Salon + yemek 24,13 · Amerikan mutfak 9,92 · Misafir/çalışma odası (yatak 4) 10,54 · Antre 7,24 (3,15 m geniş) · Hol 2,72 · WC/duş 3,42 (yan holden, girişten görünmez) · Merdiven altı kiler 2,99 · Merdiven 3,41 · **Net 64,38** |
| 1. kat | Ebeveyn yatak odası 14,44 · Giyinme odası 4,16 · Ebeveyn banyosu 4,90 · Yatak odası 2 10,54 · Yatak odası 3 10,71 · Ortak banyo 5,42 · Hol 6,80 · Merdiven 7,15 · **Net 64,13** |
| Balkonlar | Ön 10,24 (6,40 × 1,60) · Arka 9,60 (6,40 × 1,50) |

Brüt: 2 × 72,60 + 19,84 balkon = **165,04 m²**. Net kapalı alan 128,50 m².
Ön balkon vaziyet planına ve 3B modele de işlenmiştir; yanlarında 1. kat mahremiyet duvarları vardır.

## Cephe görünüşleri

`python cephe.py` ile üretilir (A1 yatay). Pencere, kapı ve balkon kapıları `kat_plani.cephe_aciklari()`
fonksiyonundan gelir; 3B model de aynı tanımı kullandığı için plan, cephe ve model birbiriyle tutarlıdır.

Kotlar: ±0,00 bahçe/otopark · +0,45 zemin kat · +3,60 1. kat · +6,75 betonarme çatı döşemesi · +7,05 bitmiş çatı · +7,65 parapet.
Malzeme: mantolama üzeri açık bej sıva, gri doğal taş subasman, betonarme düz çatı (parapetli), antrasit alüminyum doğrama,
100 cm cam balkon korkuluğu.

## Ayrık blok alternatifleri (bloklar arası 6 m)

`python vaziyet.py C|D|E` ile üretilir (`VARYANTLAR` sözlüğü). Sıralar bloklara bölünür, bloklar arasında
6 m boşluk kalır. Boşluğun ön şeridinde 2 misafir otoparkı (2,5 × 5,0 m) bulunur; geri kalanı blok sonundaki
iki villanın yan bahçesidir ve ortasından 1,90 m mahremiyet duvarı geçer.

| | B (mevcut) | C | D | E |
|---|---|---|---|---|
| Villa | 32 | 32 | 30 | 28 |
| Blok (A / B sırası) | 16 / 16 | 8+8 / 8+8 | 8+7 / 7+8 | 5+4+5 / 5+4+5 |
| Villa cephesi | 6,60 | 6,25 | 6,60 | 6,60 |
| 4+1 kat planı | uyar | daraltılmalı | uyar | uyar |
| Misafir otoparkı | 0 | 4 | 4 | 8 |
| Yan bahçeli köşe villa | 0 | 4 | 4 | 8 |
| En uzun blok | 105,6 m | 50,0 m | 52,8 m | 33,0 m |
| KAKS (165 m²/villa) | 0,83 | 0,83 | 0,77 | 0,72 |

Kuşbakışı ve giriş görselleri: `render/alternatifler/`. 3B modeller: `model_169-1-2_C/D/E.glb` ve `.html`.
