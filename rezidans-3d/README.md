# Rezidans 3B Model

Paylaşılan dört renderdan (kuşbakışı, ticari cadde, köşe perspektifi, havuz) çıkarılmış,
tarayıcıda gezilebilir Three.js modeli. Tek dosya: `index.html`.

## İçerik
- 3 konut bloğu (A, B: zemin + 7 kat; C: ticari podyum üzerinde 6 kat), beyaz döşeme
  bantları, alt LED şeritleri, cam korkuluklu köşe balkonları, beyaz çekirdek
- Kavisli uçlu ticari podyum: Restaurant, Coffee Shop, Patisserie, Store, Market
- Havuz + ahşap deck, servi sırası, fıstık çamları, pergolalar, çevre duvarı, N pilonu
- Kavisli yol, aydınlatma direkleri, park ve hareket eden araçlar, çevre ormanı

## Gezinme
- **Gezin**: sürükle döndür, sağ tık kaydır, tekerlek yakınlaş, çift tık odaklan
- **Yürü** (`M`): WASD / ok tuşları, Shift koş, sürükleyerek bak; dokunmatikte sanal çubuk
- **Kamera açıları** `1`–`6`, **Tur** `T`, **Işık** (gündüz/akşam/gece) `L`
- Vaziyet planına tıklayarak ışınlanma; URL `#cadde`, `#havuz` gibi açıyla açılır

## Çalıştırma
Herhangi bir statik sunucu yeterli: `python3 -m http.server` → `http://localhost:8000/rezidans-3d/`.
Three.js 0.160.0 jsDelivr CDN'den yüklenir.

Ölçüler renderlardan tahmin edilmiştir; model temsilidir.
