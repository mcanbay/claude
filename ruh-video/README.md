# Seni sen yapan şey nedir? · İsrâ 85

Defter/kareli kâğıt tarzında, el yazısı animasyonlu dikey (1080×1920) kısa video.
Konu: ruh, bilinç, benlik ve insanın mahiyeti — İsrâ Sûresi 85. ayet.

Seslendirme: ElevenLabs (`eleven_v4`, ses: "AHMET AKYALÇIN PRO").

## Dosyalar

| Dosya | Görev |
|---|---|
| `script_data.py` | Seslendirme metni, altyazı parçaları hâlinde |
| `assets/voice.mp3` | ElevenLabs seslendirmesi |
| `align.py` | Sesteki duraklamaları bulup metinle hizalar → `assets/timings.json` (kelime bazlı zamanlar) |
| `index.html` | Tüm sahneler (HTML/SVG); `render(t)` her zaman anını deterministik çizer |
| `render.js` | Playwright/Chromium ile kare kare render + ffmpeg ile mp4 |
| `fonts/` | Kalam, Caveat, Amiri (SIL OFL, fontsource) |

## Çalıştırma

```bash
python3 align.py assets/voice.mp3 assets/timings.json   # zamanlama
node render.js preview 12 45 70                         # test kareleri -> out/
node render.js video                                     # out/seni_sen_yapan.mp4
```

Sahnelerin animasyonları kelimelere bağlı (`S('chunk_id')`), bu yüzden seslendirme
değişirse sadece `align.py` tekrar çalıştırılır; animasyonlar kendiliğinden kayar.
