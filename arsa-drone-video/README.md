# Arsa Tanıtım Videosu: Dron Tarzı Uydu Uçuşu

**Bursa / Nilüfer / Odunluk Mahallesi, 4632 Ada, 9 Parsel** için hazırlanmış bir tanıtım videosu üreticisi.

Araç parsel sınırını TKGM Parsel Sorgu servisinden ya da TKGM'den indirilmiş KML/GeoJSON dosyasından alır. Uydu görüntüsü olarak **Esri Wayback arşivinde parselin en güncel tarihli çekimini** kendisi bulur ve bu çekimin tarihini videoya yazar. Bunlardan **dron uçuşu hissi veren** 52 saniyelik bir MP4 üretir:

| Süre | Sahne |
|---|---|
| 0–6 sn | Yüksekten açılış, başlık: *4632 Ada · 9 Parsel*, *Odunluk Mahallesi · Nilüfer / Bursa* |
| 6–17 sn | Parsele doğru dalış; kamera eğilir, parsel sınırı altın renkte çizilir |
| 17–34 sn | Parselin etrafında 360° yörünge (orbit), parsel etiketi ve yüzölçümü bandı |
| 34–47 sn | Tepeden (kuzey yukarı) görünüm: kenar uzunlukları, ölçek çubuğu, bilgi kartı |
| 47–52 sn | Kapanış kartı: başlık, yüzölçümü, iletişim bilgisi |

Ek olarak ilan sitelerinde kullanılabilecek bir **kapak görseli** (`.kapak.jpg`) çıkar. Arkada telifsiz, sentezlenmiş sakin bir müzik çalar.

> Not: Bu, gerçek bir dron çekimi değildir. Video uydu görüntüsünden oluşturulmuş bir sanal uçuştur ve kapanışta bunu belirten bir not yer alır. Gerçek dron çekimi için SHGM kayıtlı bir İHA pilotuyla çekim yapılması gerekir. O görüntüler de bu videonun yanında kullanılabilir.

## Kurulum

1. Python 3.9 veya daha yeni bir sürüm ile **ffmpeg** kurulu olmalıdır.
   - Windows: `winget install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Ubuntu: `sudo apt install ffmpeg`
2. Gerekli Python paketlerini kurun:
   ```bash
   pip install -r requirements.txt
   ```

## Çalıştırma

TKGM Parsel Sorgu'dan indirilen KML dosyasıyla (önerilen):

```bash
python drone_video.py --kml tkgm-parsel-sorgu-sonuc-4632-ada-9-parsel.kml \
    --title "Satılık Arsa" --contact "0 5xx xxx xx xx · Ad Soyad"
```

KML'deki il, ilçe, mahalle, ada, parsel, alan, nitelik ve pafta bilgileri otomatik okunur. KML vermezseniz araç sınırı TKGM servisinden çekmeyi dener. Varsayılan değerler zaten 4632 ada 9 parsele ayarlıdır.

### Görüntü tarihi

Araç Esri Wayback arşivindeki son 15 yayını tarar ve parselin bulunduğu noktadaki **çekim tarihlerini** listeler. Bunlar arasından en yeni çekimi seçer:

```
  Wayback 2026-10-29: çekim 2025-xx-xx Maxar
  Wayback 2026-09-24: çekim 2025-xx-xx Maxar
  ...
Seçilen: Wayback 2026-10-29 yayını, çekim tarihi 2025-xx-xx
```

Çekim tarihi bilgi kartında ("Görüntü tarihi") ve kaynak satırında gösterilir. Belirli bir yayını kullanmak için `--wayback-release 2026-09-24` verilebilir.

Çıktılar `cikti/` klasörüne yazılır:
- `arsa_4632_9.mp4`: 1920×1080 video
- `arsa_4632_9.kapak.jpg`: kapak görseli
- `parsel_4632_9.geojson`: TKGM'den alınan parsel sınırı

Diğer seçenekler:

| Seçenek | Açıklama |
|---|---|
| `--vertical` | Instagram Reels / YouTube Shorts / hikâye için dikey 1080×1920 |
| `--preview` | Hızlı deneme: yarı çözünürlük, 24 fps |
| `--title "..."` | Üst başlık (varsayılan: *Arsa Tanıtımı*) |
| `--contact "..."` | Bilgi kartında ve kapanışta gösterilecek iletişim bilgisi |
| `--music dosya.mp3` / `--no-music` | Kendi müziğinizi kullanın ya da müziği kapatın |
| `--wayback-release YYYY-AA-GG` | En günceli yerine belirli bir Wayback yayını |
| `--detail-zoom 18` | Bölgede zoom 19 görüntüsü yoksa daha düşük detay seviyesi |
| `--il --ilce --mahalle --ada --parsel` | Başka bir parsel için |

Tam çözünürlükte üretim sıradan bir bilgisayarda 5–10 dakika sürer. İlk çalıştırmada yaklaşık 1.000 uydu karosu indirilir ve `.karo_onbellek/` klasöründe saklanır. Sonraki denemeler bu sayede hızlıdır.

## TKGM'ye erişilemezse

TKGM servisi zaman zaman yurt dışı IP'leri veya yoğun istekleri engelleyebilir. Bu durumda sınırı kendiniz verebilirsiniz:

1. [parselsorgu.tkgm.gov.tr](https://parselsorgu.tkgm.gov.tr) adresinde parseli bulun: Nilüfer → Odunluk → 4632 / 9.
2. Sayfadaki indirme/dışa aktarma seçeneğiyle parseli **GeoJSON** veya **KML** olarak kaydedin.
3. Dosyayı araca verin:
   ```bash
   python drone_video.py --geojson parsel.geojson --contact "..."
   # veya
   python drone_video.py --kml parsel.kml --contact "..."
   ```

Köşe koordinatlarını doğrudan da girebilirsiniz:

```bash
python drone_video.py --coords "40.2227,28.9847; 40.2226,28.9854; 40.2221,28.9855; 40.2220,28.9850"
```

## Kaynaklar ve lisans notu

- Parsel sınırı: Tapu ve Kadastro Genel Müdürlüğü (TKGM) Parsel Sorgu.
- Uydu görüntüsü: Esri World Imagery / Wayback arşivi (Esri, Maxar, Earthstar Geographics). Videoda kaynak gösterimi otomatik olarak yer alır. Ticari reklam kullanımında Esri'nin kullanım koşullarını kontrol edin. `--tile-url` ile lisansına sahip olduğunuz başka bir XYZ karo kaynağı da kullanılabilir.
- Ekrandaki bilgiler tanıtım amaçlıdır. Resmî bilgi için tapu kayıtları esas alınmalıdır.
