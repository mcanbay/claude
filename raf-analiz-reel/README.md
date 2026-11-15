# Raf Analiz Reel: 100 TL Altında Sağlıklı Ara Öğünler

**Raf Analiz** için hazırlanmış 47,5 saniyelik dikey Instagram Reel (1080×1920, 30 fps). Bütün animasyon tek bir HTML dosyasında, tek bir zaman çizelgesinden üretilir. Aynı dosya hem tarayıcıda oynatılabilen bir önizleme hem de MP4'e dönüştürülen kaynaktır.

| Süre | Sahne | İçerik |
|---|---|---|
| 0–5 sn | Kanca | Market rafında hızlı kamera savrulması. *100 TL ALTINA SAĞLIKLI ARA ÖĞÜN BULABİLİR Mİ?* Barkod okuyucu ışığı rafı tarar; 100 TL altındaki etiketler sararır, üstündekilerin üzeri çizilir. |
| 5–11 sn | Kural | Bölünmüş ekran. Solda **paketin önü**: "FIT", "LIGHT", "%100 DOĞAL" gibi etiketler, altında *Sadece 'FIT' yazıyor diye alma*. Sağda **paketin arkası**: besin değerleri tablosu, büyüteç, *İçeriğe ve tok tutma gücüne bak*. Tarama geçince sol taraftaki iddia etiketleri düşer. |
| 11–31 sn | Analiz | Dört kategori kartı (her biri 5 sn): örnek raf fiyatı etiketi, porsiyon başı fiyat, 100 TL altı rozeti; pratiklik, tokluk ve içerik kalitesi puan çubukları; raf notu ve "etikette bak" maddeleri. |
| 31–38 sn | Karar | Dört ürün aynı rafta. *EN İYİ ARA ÖĞÜN = TEK BİR ÜRÜN DEĞİL*, ardından *PROTEİN + LİF + DENGELİ PORSİYON*. |
| 38–47,5 sn | Soru | *Bir sonraki Raf Analiz hangi ürün grubunu incelesin?* A) Proteinli içecekler, B) Çikolatalar, C) Granolalar. Kapanış logosu ve bilgilendirme notu. |

Videoda kasa okuyucusu bip sesi, geçiş sesleri, puan çubuğu tıkları ve fiyat zili gibi efektler de var. Bunlar da aynı zaman çizelgesinden üretilir. Müzik eklenmedi: Instagram'da müzik kitaplığından parça seçip orijinal sesin seviyesini ayarlayabilirsiniz.

## Seslendirme

Seslendirme metni, sahne zamanlaması ve kayıt notları [`seslendirme/README.md`](seslendirme/README.md) dosyasında. Kayıt (tek dosya ya da satır başına dosyalar) hazır olduğunda:

```bash
node seslendirme.js kayit.wav
node render.js
```

`seslendirme.js` satırları ayırıp videodaki yerlerine koyar ve `seslendirme/seslendirme.wav` dosyasını yazar. `render.js` bu dosya varsa efektleri konuşmanın altında kısarak karıştırır ve sesi Instagram'ın ses seviyesine (−15 LUFS) getirir.

## Kurulum

1. **Node.js 18** veya daha yeni bir sürüm ile **ffmpeg** kurulu olmalıdır.
   - Windows: `winget install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Ubuntu: `sudo apt install ffmpeg`
2. Bu klasörde:
   ```bash
   npm install
   npx playwright install chromium
   ```

## Videoyu üretme

```bash
node render.js
```

Çıktılar `cikti/` klasörüne yazılır:
- `raf-analiz-100tl.mp4`: 1080×1920, 30 fps, H.264 + AAC (Instagram'a doğrudan yüklenebilir)
- `raf-analiz-100tl.kapak.png`: Reel kapağı olarak kullanılabilecek 3. saniye karesi

| Seçenek | Açıklama |
|---|---|
| `--preview` | Hızlı deneme: yarı çözünürlük, 15 fps |
| `--fps 24` | Farklı kare hızı |
| `--cover 3.0` | Kapak görselinin alınacağı saniye |
| `--frames 3,14,33` | Yalnızca seçilen saniyelerin PNG karelerini üret |
| `--sessiz` | Efekt sesleri olmadan (sessiz ses kanalıyla) |
| `--ses-wav` | Son ses karışımını ayrıca `.wav` olarak da kaydet |
| `--yalnizca-ses` | Video üretmeden yalnızca son ses karışımını `.m4a` olarak çıkar |
| `--seslendirmesiz` | Seslendirme dosyası olsa bile yalnızca efektler |
| `--out dosya.mp4` | Çıktı dosyasının adı |

Tam çözünürlükte üretim birkaç dakika sürer. Yazı tipleri (Archivo, IBM Plex Mono) Google Fonts'tan yüklendiği için internet bağlantısı gerekir.

## Önizleme

`reel.html` tarayıcıda açılabilen bir oynatıcı içerir: oynat/duraklat, zaman çizelgesi, sahne listesi, ses aç/kapat ve **Instagram arayüzünü göster** seçeneği. Bu seçenek, Reels ekranındaki üst başlık, sağdaki beğen/yorum düğmeleri ve alttaki açıklama alanının yaklaşık yerini gösterir. Önemli yazılar bu alanların dışında kalacak şekilde yerleştirildi.

Klavye: boşluk tuşu oynat/duraklat, sol/sağ ok ±2 saniye.

## İçeriği güncelleme

Fiyatlar, aralıklar, puanlar ve notlar `reel.html` içindeki `CATS` listesindedir:

```js
{ key:'bar', name:['Meyve ve','kuruyemiş barı'],
  unit:'ADET', price:44.90, range:'35–65 TL / adet', serving:'Porsiyon (1 adet)', perServing:'45 TL',
  edge:false,            // true → rozet "100 TL ALTI · SINIRDA" olur
  rates:[5,3,3],         // pratiklik, tokluk, içerik kalitesi (5 üzerinden)
  ext:[0,0,0],           // taralı ek puan (ör. yanına protein kaynağı eklenince)
  note:'...', look:['Kuruyemiş oranı','Eklenmiş şeker'] }
```

Değişiklikten sonra `node render.js` ile videoyu yeniden üretin.

## İçerik notu

- **Fiyatlar örnektir.** Paylaşmadan önce raftaki güncel fiyatlarla değiştirin. Videoda "örnek raf fiyatı" olarak etiketlenirler.
- Puanlar **kategori geneli** içindir, tek tek ürünleri ya da markaları değerlendirmez. Kartlarda "Kategori geneli değerlendirme · Ürüne göre değişir" notu yer alır.
- Dil bilerek temkinli tutuldu ("tokluğa katkı sağlayabilir", "tok tutması sınırlı"). Videoda zayıflatma, hastalık ya da tedavi iddiası yoktur.
- Kapanışta *"Genel bilgilendirme içindir; tıbbi ya da beslenme tavsiyesi değildir."* notu bulunur.
- Ürün görselleri temsili çizimdir. Hiçbir gerçek marka, logo ya da ambalaj kullanılmadı.
