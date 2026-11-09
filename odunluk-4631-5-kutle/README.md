# Odunluk · 4631 Ada 5 Parsel — Kütle Çalışması

Verilen üç AutoCAD çıktısından (vaziyet + zemin kat planı, normal kat planı, şematik görünüş) kurulmuş 3B kütle modeli ve render görüntüleri.

**Kural:** Modelde çizimlerde olmayan hiçbir eleman yoktur: ağaç, insan, komşu bina, peyzaj, cephe rengi ya da ek kat eklenmedi. Çizimin söylemediği yerlerde en nötr seçenek kullanıldı; bunlar aşağıda tek tek listelenmiştir.

## Görüntüler (`renders/`, 3200×2000)

| Dosya | İçerik |
|---|---|
| `01_kuzeydogu_kusbakisi.png` | 706. Sokak – Odunluk Caddesi köşesinden kuşbakışı |
| `02_706_sokak_cephesi.png` | Kuzey cephe; şematik görünüşün perspektif karşılığı |
| `03_706_sokak_yaya_bakisi.png` | 706. Sokak'tan göz hizası (1,70 m) |
| `04_guneybati_kusbakisi.png` | Arka (güney) cephe ve balkonlar |
| `05_vaziyet_ustten.png` | Üstten vaziyet: parsel, otoparklar, sokak adları |
| `06_kullanim_semasi.png` | Kullanıma göre boyanmış kütle: kat etiketleri, kotlar, özet |

`index.html` aynı modeli tarayıcıda döndürülebilir olarak açar. Görünüm düğmeleri ve "Kullanım şeması" geçişi vardır. Adresin sonuna `#sokak`, `#kose`, `#guneybati`, `#vaziyet` ya da `#sema` eklenirse sayfa doğrudan o görünümle açılır.

## Çizimlerden alınan ölçüler

**Ölçek.** Zemin kat planında 1 PDF birimi = 1,96 cm. İki bağımsız kontrol aynı sonucu verir:
- Dükkan iç ölçüsü 17,27 × 5,47 m = **94,50 m²**, plandaki yazıyla birebir.
- Merdiven basamağı 14,28 birim = **28 cm** ("18 RIHT 16,38×28").

Normal kat planı biraz farklı ölçekte çizilmiş. Parsel köşeleri üzerinden zemin kat planına oturtuldu; en büyük sapma 3 mm. Oda alanları da tutuyor: Oda 13,18 m² için ölçülen 13,16; Salon 21,52 m² için 21,48.

**Kotlar (şematik görünüş).**

| Kat | Kot | Kullanım (plan) |
|---|---|---|
| Otopark katı | ±0.00 | Zemin kat planı: otopark (3 araç), sığınak ve ortak alan, ortak alan, kat holü, asansör |
| Zemin kat | +3.00 | Normal kat planı: 4 daire |
| 1. kat | +6.00 | Normal kat planı: 4 daire |
| 2. kat | +9.00 | Normal kat planı: 4 daire |
| Çatı | +12.00 | Parapet 1,00 m, üst kot +13.00 |
| Dükkan bloğu | +4.50 | Parapet 0,90 m, üst kot +5.40 |

Görünüşte en alt kata "OTOPARK KATI", üstündekine "ZEMİN KAT" deniyor. Bu nedenle "Zemin Kat Planı" adlı pafta otopark katı olarak, normal kat planı ise zemin, 1. ve 2. kat olarak okundu. Toplam 12 daire var. Her daire: salon ve mutfak 21,52 + oda 13,18 + oda 8,91 + hol 6,35 + banyo 4,20 + balkon 6,75 m² (2+1).

**Kütle.**
- Konut bloğu 25,06 m boyunda. Otopark katı 11,34 m derinliğinde; normal katlar 13,34 m.
- Normal katların uç bölümleri (köşe balkonları ve 8,91 m²'lik odalar) kuzeyde ve güneyde otopark katından 1,00 m dışarı taşar.
- Merdiven/asansör çekirdeğinin önünde iki girinti var: kuzeyde 2,50 × 1,32 m, güneyde 2,50 × 2,42 m. Her ikisi de otopark katından çatıya kadar iner.
- Dükkan bloğu 17,58 × 5,78 m ve konut bloğunun doğu duvarına bitişik.
- Kuzey cephe vitrini görünüşten alındı: 1,00 m aralıklı dikmeler, 0,50 m aralıklı kayıtlar, 4,00 m cam yüksekliği, 1,00 × 2,00 m üç kapı. Vitrin, blok uçlarından 0,50 m içeride başlar.

**Pencereler.** Plandaki 12 pencere yeri her katta tekrarlanır: kuzeyde 6, güneyde 6, toplam 36 pencere.
- Ölçü 200/220, iki kanat alüminyum profil.
- Oda pencerelerinde 90 cm alüminyum-cam korkuluk (temperli reflekte cam) ve 3 cm mermer denizlik var.
- Salon pencereleri balkona açılır.

**Arsa.**
- Parsel sınırı, komşu taraftaki çift çizgi ve 9 + 4 açık otopark yeri plan koordinatlarından alındı.
- Parsel, çizimden ölçüldüğü haliyle yaklaşık 1.082 m². Bu tapu değeri değildir.

## Çizimin söylemediği, nötr bırakılan noktalar

- **Renk / malzeme:** Cephe rengi verilmediği için duvarlar beyaz, doğrama alüminyum gri, camlar koyu bırakıldı. "Kullanım şeması" görüntüsündeki renkler yalnızca kullanım ayrımı içindir.
- **Balkon parapeti:** Görünüşte korkuluk çizilmemiş ve salon penceresinin alt kısmı kapalı görünüyor. Bu yüzden 90 cm dolu parapet olarak modellendi (15 cm kalınlık).
- **Güney cephe:** Görünüşü verilmedi. Plandaki pencere yerleri kuzeyle simetrik olduğu için kuzey cephedeki pencere tipleri kullanıldı.
- **Doğu / batı cepheler:** Planlarda bu cephelerde pencere yok, sağır bırakıldı. Dükkanın kuzey dışındaki cepheleri de sağır.
- **Bina girişi:** Görünüşte "BİNA GİRİŞİ" yazısı var ama kapı çizilmemiş. Çekirdek önündeki girinti boş bırakıldı.
- **Yollar:** Genişlikleri çizimde yok. Asfalt, parsel sınırından maket tablasının kenarına kadar temsili olarak gösterildi.
- **Sınır duvarı:** Çift çizginin yüksekliği verilmediği için zeminde ince bir bant olarak gösterildi.
- **İç mekân** modellenmedi; otopark katındaki 3 kapalı araç yeri de buna dahil. Duvar kalınlığı yalnızca pencere derinliği için 25 cm alındı.
- **Görünüş ile plan arasındaki fark:** Şematik görünüşte konut genişliği 24,92 m, planda 25,06 m (14 cm fark). Plan esas alındı.

## Yeniden üretmek

```bash
npm install            # three@0.160.0 (+ playwright)
node render.mjs        # renders/*.png, varsayılan 1600×1000 @2x
node render.mjs 1920 1080 1
GORUNUS=vaziyet node render.mjs   # tek görünüm
```

Etkileşimli görüntüleyici için klasörü herhangi bir statik sunucuyla açın (ör. `npx serve .`) ve `index.html`'i tarayıcıda görüntüleyin. three.js jsDelivr'dan yüklenir.

Dosyalar:
- `kutle.js`: bütün koordinatlar, kotlar ve geometri.
- `index.html`: sahne, ışık, kameralar ve arayüz.
- `render.mjs`: Playwright ile ekran görüntüsü alır.
