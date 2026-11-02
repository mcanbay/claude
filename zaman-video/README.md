# Allah katında zaman nedir? · Hac 47 · Secde 5

`ruh-video` ile aynı defter tarzı ve aynı motor. Konu: zamanın izafiliği
(görelilik, GPS saatleri) ve Kur'an'daki ilahi zaman anlayışı
(Hac 47, Secde 5, Meâric 4, Mü'minûn 112–113).

Seslendirme: yerel **VoxCPM2** motoru ([voxcpm2-turkce-ses-tasarimi](https://github.com/alexturkey/voxcpm2-turkce-ses-tasarimi)),
hazır ses **"Tok Sesli Anlatıcı"** (metin tarifinden tasarlanmış yapay ses, kimsenin klonu değil), CPU'da üretildi.
Motorun okuduğu metin: `seslendirme_satirlar.txt` (satır = cümle, `|| paragraf` = durak).

## Akış

```bash
# 1) ses yokken: tahmini zamanlama ile sessiz taslak
python3 synth_timings.py assets/timings.json
node render.js video            # -> out/taslak_sessiz.mp4

# 2) VoxCPM2 ile seslendirme (ses deposunun kökünde)
python3 -m ses_tasarim.oku --ayarlar ayarlar.json --ses hazir/tok_anlatici \
    --metin @seslendirme_satirlar.txt --cikti cikti/
#    -> okuma.wav + ozet.json (satır başı/sonu zamanları)
ffmpeg -i cikti/okuma.wav -b:a 192k assets/voice.mp3 && cp cikti/ozet.json assets/voice_ozet.json
python3 align_lines.py assets/voice.mp3 assets/voice_ozet.json assets/timings.json
node render.js video            # -> out/allah_katinda_zaman.mp4
```

`scenes.html` + `build.js` bu konuya özel sahnelerdir; `assemble.py` bunları
`../ruh-video/index.html` içindeki ortak motorla birleştirip `index.html` üretir.
