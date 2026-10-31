# Allah katında zaman nedir? · Hac 47 · Secde 5

`ruh-video` ile aynı defter tarzı ve aynı motor. Konu: zamanın izafiliği
(görelilik, GPS saatleri) ve Kur'an'daki ilahi zaman anlayışı
(Hac 47, Secde 5, Meâric 4, Mü'minûn 112–113).

Seslendirme metni: `seslendirme_metni.txt` (ElevenLabs `eleven_v4`, ses "AHMET AKYALÇIN PRO").

## Akış

```bash
# 1) ses yokken: tahmini zamanlama ile sessiz taslak
python3 synth_timings.py assets/timings.json
node render.js video            # -> out/taslak_sessiz.mp4

# 2) ElevenLabs sesi assets/voice.mp3 olarak konunca
python3 align.py assets/voice.mp3 assets/timings.json
node render.js video            # -> out/allah_katinda_zaman.mp4
```

`scenes.html` + `build.js` bu konuya özel sahnelerdir; `assemble.py` bunları
`../ruh-video/index.html` içindeki ortak motorla birleştirip `index.html` üretir.
