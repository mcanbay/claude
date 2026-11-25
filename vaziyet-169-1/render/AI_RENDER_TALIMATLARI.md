# Yapay zeka ile fotogerçekçi render: talimat paketi

Bu klasördeki kütle renderları, görsel üretebilen bir yapay zeka aracında (ChatGPT, Gemini, Midjourney
"image prompt" vb.) fotogerçekçi görsele dönüştürülebilir. Her görünüş için:

1. İlgili PNG dosyasını sohbete yükleyin.
2. Aşağıdaki İngilizce metni olduğu gibi yapıştırın. Bu modeller İngilizce talimatla daha tutarlı sonuç veriyor.
3. Sonucu çizimlerle karşılaştırın: villa sayısı, pencere ve kapı yerleri, balkonlar ve mahremiyet
   duvarları. Yapay zeka bazen pencere ekler, kat ekler ya da ağaçları çoğaltır. Böyle bir sapma olursa
   aynı sohbette "Keep the geometry exactly as in the uploaded image; remove the extra …" diye düzeltin.

Ortak malzeme dili (çizimlerle aynı): açık bej ince sıva (mantolama), bej kat bandı, gri doğal taş
subasman, betonarme düz çatı (60 cm parapet, açık gri alüminyum harpuşta), antrasit alüminyum doğrama,
çerçevesiz cam balkon korkuluğu,
bej sıvalı mahremiyet duvarları.

---

## 1. Kuşbakışı: `01_kusbakisi.png`

```
Intended use: photorealistic architectural visualization (real-estate marketing render) made from this simple 3D massing model of a gated townhouse site in Bursa, Turkey.

Change: turn the flat-shaded massing into a photograph-quality aerial drone render on a clear late-morning spring day. Two rows of attached two-storey townhouses facing a private 6 m asphalt site road. Facades: light warm-beige fine render, a slightly darker beige floor band, grey natural-stone plinth. Roofs: flat reinforced-concrete roofs with light-grey gravel, hidden behind a 60 cm parapet with a slim light-grey aluminium coping; a slightly darker beige band marks the concrete roof slab edge. No pitched roofs, no tiles. Windows and balcony doors: anthracite aluminium frames with real glass reflections. Balconies: concrete slabs with frameless clear glass railings. The thin walls projecting between houses are beige rendered privacy walls. Front yards: grey concrete pavers with one parked car per house (realistic modern cars in white, grey, black, navy, red). Back gardens: real lawn, stone terraces, young deciduous trees, low shrubs along the beige garden walls. Perimeter: rendered garden wall with clipped hedge. Surroundings: soft green fields and distant hazy hills instead of the empty beige ground plane. Soft natural shadows, realistic sky.

Preserve exactly: camera position, angle and framing; the number of houses in each row (16 and 16), their widths, the flat roofline and parapet height, the position of every window, balcony and privacy wall, the road layout and the site boundary shape. Do not add or remove buildings or storeys.

Constraints: no text, no labels, no watermark, no people in the foreground, no extra buildings inside the site, no swimming pools.
```

## 2. Site girişi / göz hizası: `07_girisler.png`

```
Intended use: photorealistic architectural visualization (real-estate marketing render) made from this simple 3D massing model, eye-level street view inside a gated townhouse site in Bursa, Turkey.

Change: turn the flat-shaded massing into a photograph-quality eye-level render on a clear late-morning spring day. A row of attached two-storey townhouses along a private asphalt site road with a white dashed centre line and a low kerb. Facades: light warm-beige fine render, slightly darker beige floor band, grey natural-stone plinth. Ground floor: anthracite steel front doors with a narrow vertical glass strip, anthracite aluminium windows. First floor: continuous balcony with concrete slab edge and frameless clear glass railing, large anthracite sliding balcony doors with realistic reflections. Beige rendered privacy walls project between the houses on the upper floor; low beige rendered walls with stone coping separate pairs of entrance paths. Roofline: flat concrete roof with a 60 cm parapet and slim light-grey aluminium coping, a darker beige band at the roof slab edge. No pitched roof, no tiles. Front yards: grey concrete pavers, a few potted olive trees, a wall light next to each door. Replace the box-shaped placeholder cars with realistic modern cars parked nose-in (white, grey, black, red). Opposite side of the road: the matching row of townhouses. In the distance: a young tree and soft green hills. Natural soft shadows, blue sky with light clouds.

Preserve exactly: camera position, eye height, perspective and framing; number and rhythm of houses; position of every door, window, balcony, privacy wall, entrance wall and parking bay; road width and direction. Do not add storeys or change building heights.

Constraints: no text, no labels, no watermark, no people, no extra buildings in front of the camera.
```

## 3. Bahçeden: `06_bahceden.png`

```
Intended use: photorealistic architectural visualization of a private back garden of a townhouse, made from this simple 3D massing model.

Change: photograph-quality eye-level view from the end of the garden on a warm late-afternoon summer day. Light warm-beige rendered facade, grey stone plinth, a large anthracite aluminium sliding glass door on the ground floor opening onto a stone-paved terrace with an outdoor dining table for six and a parasol. First floor: balcony with frameless glass railing and an anthracite sliding door, beige rendered privacy walls between neighbouring balconies. On both sides of the terrace: 2.4 m high beige rendered privacy walls with stone coping, lowering to 1.9 m along the garden. Lush lawn, a young olive or maple tree, lavender and boxwood planting along the walls, warm interior lights glowing softly. Above: flat roof parapet with slim light-grey aluminium coping (no pitched roof).

Preserve exactly: camera position and framing, the wall heights and positions, the door and window positions, the balcony and the neighbouring houses' privacy walls. Do not open views into the neighbouring gardens; the walls must keep full privacy.

Constraints: no text, no watermark, no people, no swimming pool.
```

## 4. Arka bahçeler / sıra: `04_arka_bahceler.png`

```
Intended use: photorealistic architectural visualization (real-estate marketing render) made from this simple 3D massing model of the garden side of two rows of townhouses.

Change: photograph-quality elevated view on a clear spring morning. Light warm-beige rendered facades, grey stone plinth, flat reinforced-concrete roofs with gravel behind 60 cm parapets and light-grey coping, anthracite aluminium sliding doors and windows with reflections, first-floor balconies with frameless glass railings and beige privacy walls between them. Each house has its own garden separated by beige rendered walls (2.4 m next to the terrace, 1.9 m further out): stone terraces, lawn, small trees and shrubs, some garden furniture. Perimeter garden wall with a clipped hedge. Soft natural shadows, realistic sky, hazy green hills in the background.

Preserve exactly: camera position and framing, number of houses, the flat roofline, the position of every window, balcony and wall. Do not add storeys or buildings.

Constraints: no text, no watermark, no people, no swimming pools.
```

---

## Geometriyi koruyan alternatif: kendi render motorumuz

Yapay zeka görselleri hızlı ve etkileyicidir, ama ölçü ve detay sadakati garanti değildir. Projeye birebir
sadık bir görsel için `model_169-1-2_B.glb` dosyası Blender (ücretsiz) veya Lumion/Twinmotion/D5 Render'a
aktarılıp gerçek malzeme ve gün ışığıyla render alınabilir. Bu render ilan görsellerinin yapay zekayla
hazırlanacak versiyonları için de iyi bir referanstır.
