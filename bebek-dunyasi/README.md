# Bebeğin Dünyasında Bir Gün · Bölüm 1

**"Mama Sandalyesi mi, Uzay Gemisi mi?"**: 30 saniyelik, dikey (9:16) bir çizgi film. Instagram Reels, TikTok ve YouTube Shorts için hazırlandı.

Video tamamen kodla çizilir ve canlandırılır. Görsel ya da video üretmek için yapay zekâ kullanılmaz, kredi harcanmaz. Müzik ve ses efektleri de kodla sentezlenir (telifsiz).

| Süre | Sahne |
|---|---|
| 0–3 sn | **Gerçek dünya.** Anne bebeği mama sandalyesine oturtur: *"Haydi bakalım, yemek zamanı!"* Bebek kocaman gözlerle etrafına bakar. |
| 3–8 sn | **Hayal dünyası.** Bebeğin gözlerinden açılan ışıltılı bir daireyle ortam uzaya dönüşür. Mama sandalyesi ışıkları yanıp sönen bir pilot koltuğuna, tepsi kontrol paneline dönüşür, bebeğin başına kask gelir. İç ses: *"Annem bunun sadece bir mama sandalyesi olduğunu düşünüyor… Ama benim için… görev başlıyor."* |
| 8–13 sn | **Uzaya fırlama.** Kaşık kontrol koluna dönüşür. Sandalyenin bacakları iticilere dönüşüp ateş alır, yıldızlar iz bırakarak akar. Ardından nişangâh kilitlenir: **HEDEF TESPİT EDİLDİ: BROKOLİ GEZEGENİ 🥦** |
| 13–20 sn | **Büyük karşılaşma.** Halkalı dev brokoli gezegeni dramatik müzikle yaklaşır: *"Daha önce hiç karşılaşmadığım bir yaşam formu…"* Bebek düşünür, sonra burnunu kaldırıp başını çevirir: *"Bunu araştırmak için henüz hazır değilim."* |
| 20–26 sn | **Gerçek dünyaya dönüş.** Hayal baloncuğu söner. Anne brokolili kaşığı sabırla uzatır: *"Hadi bir kaşık daha…"* Bebek kameraya döner, kamera yüzüne yaklaşır, cırcır böcekleri öter. Düşünce balonu: *"Anne… sen hiçbir şey bilmiyorsun."* |
| 26–30 sn | **Kapanış.** *"Sizin için sıradan bir gün… Onlar için kocaman bir macera."* Küçük bir roket uçar. Alt satırda: **BEBEĞİN DÜNYASINDA BİR GÜN \| BÖLÜM 1** |

Replikler konuşma balonu, düşünce balonu ve altyazı olarak ekranda görünür. Böylece video sesi kapalı izlendiğinde de anlaşılır.

**Hazır çıktı:** [`video/bolum1_mama_sandalyesi.mp4`](video/bolum1_mama_sandalyesi.mp4) (seslendirmesiz; müzik ve efektler var) ve kapak görseli [`video/bolum1_mama_sandalyesi.kapak.jpg`](video/bolum1_mama_sandalyesi.kapak.jpg).

## Kurulum

1. Python 3.9 veya daha yeni bir sürüm ile **ffmpeg** kurulu olmalıdır.
   - Windows: `winget install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Ubuntu: `sudo apt install ffmpeg`
2. Python paketlerini kurun:
   ```bash
   pip install -r requirements.txt
   ```

## Çalıştırma

```bash
python bolum1.py
```

Çıktılar `cikti/` klasörüne yazılır:
- `bolum1_mama_sandalyesi.mp4`: 1080×1920, 30 fps, 30 sn video
- `bolum1_mama_sandalyesi.kapak.jpg`: kapak görseli (başlıklı)

Tam çözünürlükte üretim sıradan bir bilgisayarda birkaç dakika sürer.

| Seçenek | Açıklama |
|---|---|
| `--preview` | Hızlı deneme: 540×960, 15 fps |
| `--kare 17.5` | Yalnızca o saniyedeki kareyi PNG olarak kaydeder |
| `--kapak` | Yalnızca kapak görselini üretir |
| `--seslendirme klasör` | Seslendirme kayıtlarının klasörü (varsayılan: `seslendirme/`) |
| `--muzik-yok` | Müziği ve efektleri kapatır |
| `--cikti dosya.mp4` | Çıktı dosyasının yolu |

## Seslendirme eklemek

`seslendirme/` klasörüne aşağıdaki adlarla ses dosyası koyup komutu yeniden çalıştırın. Dosyalar `.wav`, `.mp3`, `.m4a`, `.ogg` ya da `.flac` olabilir. Her kayıt kendi anında başlar, konuşma süresince müzik kendiliğinden kısılır. Kayıt başındaki ve sonundaki sessizlik otomatik kırpılır. Eksik dosya sorun değildir: o replik yalnızca yazı olarak kalır.

| Dosya adı | Başlangıç | En uzun | Kim | Replik |
|---|---|---|---|---|
| `01_anne_yemek_zamani` | 0,45 sn | 2,5 sn | Anne | Haydi bakalım, yemek zamanı! |
| `02_bebek_mama_sandalyesi` | 3,35 sn | 2,9 sn | Bebeğin iç sesi | Annem bunun sadece bir mama sandalyesi olduğunu düşünüyor… |
| `03_bebek_gorev_basliyor` | 6,35 sn | 1,6 sn | Bebeğin iç sesi | Ama benim için… görev başlıyor. |
| `04_bebek_yasam_formu` | 14,0 sn | 2,9 sn | Bebeğin iç sesi (ciddi, belgesel tonu) | Daha önce hiç karşılaşmadığım bir yaşam formu… |
| `05_bebek_hazir_degilim` | 17,75 sn | 2,2 sn | Bebek | Bunu araştırmak için henüz hazır değilim. |
| `06_anne_bir_kasik_daha` | 20,55 sn | 2,4 sn | Anne (sabırlı) | Hadi bir kaşık daha… |
| `07_bebek_hicbir_sey_bilmiyorsun` | 23,4 sn | 2,6 sn | Bebeğin iç sesi (umursamaz) | Anne… sen hiçbir şey bilmiyorsun. |

"En uzun" sütunu, kaydın bir sonraki olaya taşmadan sürebileceği yaklaşık süredir. Daha uzun bir kayıt da çalışır ama bir sonraki repliğin üzerine biner. Gerekirse `bolum1.py` içindeki `REPLIKLER` listesinden zamanlar değiştirilebilir.

Seslendirme için birkaç yol:
- **Kendi sesinizle:** Telefonun ses kaydedicisiyle her repliği ayrı ayrı kaydedip yukarıdaki adlarla kaydedin.
- **ElevenLabs:** Örneğin *Gözde Arıkan* (anne) ve *The Kid – Çocuk* (bebek) sesleriyle, `eleven_v4` modeli kullanılarak `[serious]`, `[sarcastic]`, `[softly]` gibi duygu etiketleri verilebilir. İndirilen MP3'leri yeniden adlandırıp klasöre koymanız yeterli.

## Dosyalar

| Dosya | İçerik |
|---|---|
| `bolum1.py` | Bölümün zaman çizelgesi, bebeğin pozları, kamera, geçişler, video kodlama |
| `cizim.py` | Vektör çizim altyapısı (süper örneklemeli kenar yumuşatma, afin kamera) ve karakterler: bebek, mama sandalyesi/uzay koltuğu, anne kolu, brokoli, mutfak, uzay |
| `arayuz.py` | Konuşma/düşünce balonları, altyazı, HEDEF uyarı paneli, nişangâh, kapanış kartı |
| `ses.py` | Sentezlenmiş müzik ve efektler, seslendirme karıştırma |
| `fontlar/` | [Fredoka](https://fonts.google.com/specimen/Fredoka) yazı tipi (SIL Open Font License, `OFL.txt`) |

`cizim.py` ve `arayuz.py` bölümden bağımsızdır. Sonraki bölümler aynı bebek karakteriyle, yeni bir `bolumN.py` dosyası yazılarak üretilebilir.
