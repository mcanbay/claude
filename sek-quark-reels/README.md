# RAF ANALİZ #01: SEK Protein Quark (Reels / TikTok)

Bu klasörde 30 saniyelik, 9:16 dikey bir ürün inceleme videosunun tüm kaynakları var. Video Remotion (React) ile kodlandı.

| Çıktı | Dosya |
|---|---|
| Final video (1080x1920, 30 fps, H.264 + AAC, −14 LUFS) | `out/final_video.mp4` |
| Kapak görseli | `out/cover.png` |
| Senaryo, sahne ve zaman dökümü | `video_script.txt` |
| Kaynaklar ve doğrulanmış ürün verisi | `KAYNAKLAR.md` |
| Instagram ve TikTok metinleri, hashtag'ler, sabit yorum | `SOSYAL_MEDYA.md` |

## Yapı

```
src/
  timeline.json      sahne zamanları + ses efekti cue'ları (görüntü ve ses ortak kullanır)
  data.ts            doğrulanmış besin değerleri (tek kaynak)
  brand.ts           marka adı, renkler, fontlar
  ui.tsx             animasyon yardımcıları, geçiş (Wipe), ikonlar, sayaç, grain
  scenes/            Hook, Product, Nutrition, Who, Outro
  Video.tsx          ana kompozisyon
  Cover.tsx          kapak görseli
scripts/
  cutout.py          ambalaj fotoğrafının arka planını temizler, kapaktaki rozeti kırpar
  audio.py           özgün müzik + SFX sentezi (numpy/scipy, sample yok)
  build.sh           tam üretim hattı
  preview-stills.mjs seçilen karelerden hızlı önizleme
sources/             orijinal ambalaj fotoğrafı (Migros)
```

## Gereksinimler

- Node 18+, Python 3.10+ (`numpy`, `scipy`, `pillow`), FFmpeg
- `npm install`

## Komutlar

```bash
npm run studio                      # tarayıcıda canlı önizleme / düzenleme
npm run build                       # out/final_video.mp4 + out/cover.png üretir
REMOTION_CHROME=/path/to/chrome-headless-shell npm run build   # kurulu Chrome kullanmak için
```

## Düzenleme notları

- **Marka adını değiştirmek:** `src/brand.ts` dosyasındaki `BRAND` alanını düzenleyin.
- **Zamanlama:** Sahne süreleri ve ses efektleri `src/timeline.json` dosyasında. Burayı değiştirdikten sonra `npm run build` sesi de yeniden üretir.
- **Yeni ürün:** `src/data.ts` dosyasını ve `sources/` klasöründeki görseli güncelleyin, sahne metinlerini uyarlayın.
- **Lisans:** Remotion, bireyler ve en fazla 3 çalışanlı şirketler için ücretsizdir. Daha büyük ekipler için şirket lisansı gerekir (remotion.dev/license).
