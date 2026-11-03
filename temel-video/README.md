# Binanın Görünmeyen Kahramanı

Dikey (1080×1920, 30 fps) kısa animasyon. Usta binanın cephesini gösterir:
**"Herkes buraya bakıyor."** Kamera yerin altına iner, tarama çizgisiyle bodrum, radye temel
ve kazıklar görünür hâle gelir. Temel gözlerini açar: **"Ama asıl mesele benim!"**
Kapanışta yük okları çatıdan temele ve kazıklardan zemine akar, *TEMEL* etiketi ve
"Sağlam bina, sağlam temelle başlar." sloganı çıkar.

| Zaman (taslak) | Sahne |
|---|---|
| 0–1,7 sn | Başlık, cephe parıltısı, usta cepheyi gösterir |
| 1,7–3,7 sn | Usta: "Herkes buraya bakıyor." (yoldan geçenler fotoğraf çeker) |
| 4,1–6,4 sn | Kamera iner, yeraltı röntgen taramasıyla açılır |
| 6,5–9,3 sn | Temel uyanır: "Ama asıl mesele benim!" (kahraman ışınları) |
| 9,9–14,6 sn | Geri çekilme, yük okları, TEMEL etiketi, slogan |

Kesin süreler seslendirmeden hesaplanır (`zamanla.py`); sahneler satırların sesteki
uzunluğuna göre kayar. Ağızlar (usta ve temel) sesin kare başına genliğiyle oynar.

## Seslendirme

Bir önceki videoyla (`zaman-video`) aynı ses: yerel **VoxCPM2** motoru
([alexturkey/voxcpm2-turkce-ses-tasarimi](https://github.com/alexturkey/voxcpm2-turkce-ses-tasarimi)),
hazır ses **"Tok Sesli Anlatıcı"** (`hazir/tok_anlatici`, metin tarifinden tasarlanmış yapay ses,
kimsenin klonu değil). Sabit kalite: 16 adım, cfg 2.0. Motorun okuduğu metin `seslendirme_satirlar.txt`.

## Akış

```bash
# 1) ses yokken: tahmini zamanlama ile taslak (yalnız efektler)
python3 zamanla.py --taslak
node render.js video                      # -> out/taslak.mp4

# 2) VoxCPM2 ile seslendirme (ses deposunun kökünde)
python -m ses_tasarim.oku --ayarlar ayarlar.json --ses hazir/tok_anlatici \
    --metin @seslendirme_satirlar.txt --cikti cikti/
#    -> okuma.wav + ozet.json (satır başı/sonu zamanları)
ffmpeg -i cikti/okuma.wav -b:a 192k assets/okuma.mp3 && cp cikti/ozet.json assets/voice_ozet.json

# 3) satırları sahnelere yerleştir, ağız zarfı + efektler, video
python3 zamanla.py --ses assets/okuma.mp3 --ozet assets/voice_ozet.json
node render.js video                      # -> out/binanin_gorunmeyen_kahramani.mp4
```

Ara kareleri görmek için: `node render.js preview 2.6 7.0 8.9 13.5` (→ `out/preview_*.png`).

## Dosyalar

| Dosya | Görev |
|---|---|
| `index.html` | Tüm sahne (SVG). `setup(timings)` kurar, `render(t)` her anı deterministik çizer |
| `render.js` | Playwright/Chromium ile kare kare render, ffmpeg ile mp4 + ses (loudnorm −15 LUFS) |
| `zamanla.py` | Satır süreleri → sahne işaretleri, kelime zamanları, ağız zarfı; sentez efektler (parıltı, vuuş, gümleme) |
| `seslendirme_satirlar.txt` | VoxCPM2'ye verilen metin (satır = cümle, `|| paragraf` = durak) |
| `assets/timings.json` | `zamanla.py` çıktısı |
| `fonts/` | Baloo 2 (SIL OFL 1.1, fontsource) |

Karakterler, bina ve efektler bu proje için çizildi/sentezlendi; dış görsel ya da müzik yoktur.
