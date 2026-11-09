# Odunluk · 4631 Ada 5 Parsel — Kütle Çalışması

Verilen üç AutoCAD çıktısından (vaziyet + zemin kat planı, normal kat planı, şematik görünüş) kurulmuş 3B kütle modeli ve render görüntüleri.

**Kural:** Kütle modelinde çizimlerde olmayan hiçbir eleman yoktur: ağaç, insan, komşu bina, peyzaj, cephe rengi ya da ek kat eklenmedi. Çizimin söylemediği yerlerde en nötr seçenek kullanıldı; bunlar aşağıda tek tek listelenmiştir.

## Cephe tasarımı — fotogerçekçi render'lar (`renders/tasarim/`, 1920×1200)

Kütle, kotlar, pencere ve balkon düzeni çizimdeki gibi kaldı. Üzerine çağdaş ve sade bir malzeme kompozisyonu giydirildi. Malzeme geçişleri kütlenin kendi kurgusunu izler:

| Yüzey | Malzeme | Mantık |
|---|---|---|
| Çıkmalı kanatlar: köşe balkonu + 8,91 m²'lik oda kutusu | Açık, doğal tonlu dekoratif sıva | Cephenin ana yüzeyi; 1 m çıkma yapan kütleler açık okunur |
| Geri çekilmiş orta akslar: 13,18 m²'lik oda pencereleri | Koyu gri kompozit panel. Derzler pencere üst/alt hizası ve kat çizgilerinde | Girinti koyu okunur, cephe dikeyde bölümlenir |
| Yan cephelerin (doğu/batı) ortası, kat holü aksı | Aynı koyu gri panel bandı | Sağır yan duvarları ikiye böler; uzun cephelerdeki orta aksın karşılığı |
| Merdiven yarığı / bina girişi ve balkon cepleri (arka, yan duvar, tavan) | Ahşap tonlu kompozit lambri (20 cm) | Boşluklar sıcak tonla okunur; giriş vurgulanır |
| Otopark katı kaidesi ve dükkan | Antrasit kompozit panel | Konut kütlesi koyu bir kaidenin üzerinde durur; dükkan bu kaidenin devamıdır |
| Doğrama, korkuluk profilleri, parapet harpuştası | Antrasit metal | İnce, koyu çizgi detayları |
| Balkonlar | Çerçevesiz cam korkuluk: antrasit alt profil + küpeşte, 90 cm | Plandaki 90 cm korkuluk yüksekliği korundu |

Ek olarak görünüşteki "BİNA GİRİŞİ" yazısının yerine, kuzey yarığın dibine antrasit kasalı cam bir giriş kapısı (1,20 × 2,40 m) konuldu.

| Dosya | Görünüm |
|---|---|
| `kuzeydogu.png` | 706. Sokak – Odunluk Caddesi köşesinden kuşbakışı |
| `kose.png` | 706. Sokak'tan, dükkan önünden göz hizası |
| `sokak.png` | Kuzey cephe (şematik görünüşün karşılığı) |
| `batikose.png` | 706. Sokak'ın batı ucundan göz hizası, akşamüstü ışığı |
| `guneybati.png` | Arka (güney) cephe, kuşbakışı |
| `giris.png` | Bina girişi ve orta aks, yakın plan |

Render hattı: `kutle.js` "tasarim" kipinde modeli kurar. `blender/disa_aktar.mjs` modeli GLB'ye aktarır. `blender/render_cycles.py` ise Blender Cycles ile (yol izleme, fiziksel gökyüzü ve güneş, OpenImageDenoise) render alır. Malzemelerin hepsi prosedüreldir:
- sıvada ince doku,
- panellerde tek tek ton farkı,
- lambride damar,
- kilitli parke, asfalt.

Ağaç, insan, araç ve komşu bina eklenmedi; çizimlerde yoklar. Yol genişlikleri temsilidir.

## Kütle görüntüleri (`renders/`, 3200×2000)

| Dosya | İçerik |
|---|---|
| `01_kuzeydogu_kusbakisi.png` | 706. Sokak – Odunluk Caddesi köşesinden kuşbakışı |
| `02_706_sokak_cephesi.png` | Kuzey cephe; şematik görünüşün perspektif karşılığı |
| `03_706_sokak_yaya_bakisi.png` | 706. Sokak'tan göz hizası (1,70 m) |
| `04_guneybati_kusbakisi.png` | Arka (güney) cephe ve balkonlar |
| `05_vaziyet_ustten.png` | Üstten vaziyet: parsel, otoparklar, sokak adları |
| `06_kullanim_semasi.png` | Kullanıma göre boyanmış kütle: kat etiketleri, kotlar, özet |

`index.html` aynı modeli tarayıcıda döndürülebilir olarak açar. Üç kip vardır: "Cephe tasarımı" (varsayılan), "Kütle" ve "Kullanım şeması"; görünüm düğmeleri de bulunur. Adresin sonuna `#sokak`, `#kose`, `#guneybati` ya da `#vaziyet` eklenirse o görünüm açılır; `#kutle` ve `#sema` ise ilgili kipi açar.

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

Fotogerçekçi cephe render'ları (Blender'ın Python modülü gerekir):

```bash
pip install bpy==5.2.3                       # Python 3.13; Blender 5.2 LTS
node blender/disa_aktar.mjs                  # blender/model_tasarim.glb
python blender/render_cycles.py --glb blender/model_tasarim.glb --cikti renders/tasarim \
    --ornek 192 --en 1920 --boy 1200         # --gorunus kose,sokak ile tek tek
```

Etkileşimli görüntüleyici için klasörü herhangi bir statik sunucuyla açın (ör. `npx serve .`) ve `index.html`'i tarayıcıda görüntüleyin. three.js jsDelivr'dan yüklenir.

Dosyalar:
- `kutle.js`: bütün koordinatlar, kotlar ve geometri.
- `index.html`: sahne, ışık, kameralar ve arayüz.
- `render.mjs`: Playwright ile ekran görüntüsü alır.
- `blender/disa_aktar.mjs`, `blender/render_cycles.py`: fotogerçekçi render hattı.
