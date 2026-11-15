# Seslendirme metni ve kayıt notları

Video 47,5 saniye. Seslendirme 12 satırdan oluşur; her satır bir sahneye denk gelir. Kayıt hangi yolla yapılırsa yapılsın (stüdyo spikeri, ElevenLabs ya da kendi sesiniz) `seslendirme.js` satırları ayırıp videodaki yerlerine koyar.

## Ton

Güvenilir, sıcak ve enerjik bir reklam spikeri. Abartılı satış tonu yok; bağımsız bir analiz kanalı konuşuyor. Kanca merakla, kural cümlesi kararlı, karar bölümü sıcak, kapanış enerjik okunur.

## Metin

| No | Sahne | Videodaki yeri | En fazla | Metin |
|---|---|---|---|---|
| 1 | Kanca | 0,2 sn | 4,9 sn | 100 TL altına sağlıklı bir ara öğün bulabilir miyiz? |
| 2 | Kural | 5,6 sn | 2,1 sn | Sadece “fit” yazıyor diye alma. |
| 3 | Kural | 7,9 sn | 3,4 sn | Paketi çevir: içeriğe ve tok tutma gücüne bak. |
| 4 | Analiz 1/4 | 11,7 sn | 4,8 sn | Meyve ve kuruyemiş barı çok pratik. Hurma ağırlıklıysa şekere dikkat. |
| 5 | Analiz 2/4 | 16,7 sn | 4,8 sn | Protein bar tokluğa katkı sağlayabilir, ama 100 TL sınırında. |
| 6 | Analiz 3/4 | 21,7 sn | 4,8 sn | Karabuğday patlağının içeriği sade, ama tek başına hafif kalır. |
| 7 | Analiz 4/4 | 26,7 sn | 4,7 sn | Pirinç ve mısır patlağında lif ve protein düşük. Yanına protein ekle. |
| 8 | Karar | 31,55 sn | 2,3 sn | En iyi ara öğün, tek bir ürün değil. |
| 9 | Karar | 34,0 sn | 3,7 sn | Protein… lif… ve dengeli porsiyon. |
| 10 | Soru | 38,45 sn | 2,0 sn | Sıradaki Raf Analiz ne olsun? |
| 11 | Soru | 40,6 sn | 4,1 sn | Proteinli içecekler mi… çikolatalar mı… granolalar mı? |
| 12 | Soru | 44,9 sn | 1,9 sn | Yorumlara yaz! |

"En fazla" süreyi biraz aşan satırlar ses perdesi korunarak en çok %15 hızlandırılır. Daha uzun satırlar bir sonraki sahneye taşar ve araç bunu uyarı olarak yazar.

## Kayıt teslimi

İki yoldan biri:

1. **Tek dosya:** 12 satırı sırayla okuyun. Satır aralarında yaklaşık 1 saniye sessizlik bırakın. Satır içindeki duraklamalar (virgül, üç nokta) bundan kısa olmalı.
2. **Satır başına dosya:** `01.wav`, `02.wav` … `12.wav` (mp3, m4a ve flac da olur).

Mono, 44,1 veya 48 kHz, arka plan müziği olmadan.

## Videoya ekleme

```bash
node seslendirme.js kayit.wav        # ya da: node seslendirme.js satirlar/
node render.js
```

`seslendirme.js` her satırın yerleştiği zamanı ve satır içindeki duraklamaları yazdırır. 9. satırdaki duraklamalar PROTEİN / LİF / DENGELİ PORSİYON bloklarının, 11. satırdakiler A / B / C vurgusunun zamanıdır. Bunlar kayda göre değişirse `reel.html` içindeki `KW_T` ve `SEL_T` değerlerini bu sürelerin 0,25 sn öncesine ayarlayın.

Önizleme sayfasında da seslendirmeyi duymak için `seslendirme/seslendirme.mp3` dosyasını sayfayla birlikte `seslendirme.mp3` adıyla yayınlayın.

## Fiyat değişirse

5. satır protein barın 100 TL sınırına yakın olduğunu söyler. `reel.html` içindeki fiyatları değiştirirseniz bu cümlenin hâlâ doğru olduğunu kontrol edin.
