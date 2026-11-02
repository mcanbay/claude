# 4622/3 – Kütle modeli (render için)

**Program:** Zemin kat 7 dükkan (770,5 m²) + **7 normal kat × 5 daire = 35 daire** (2+1, ≈72 m² net)

| Dosya | İçerik |
|---|---|
| `kutle_testere.obj/.mtl/.glb` | Testere dişi balkonlu cephe |
| `kutle_duz.obj/.mtl/.glb` | Düz (dikdörtgen) balkonlu cephe |
| `onizleme/*.png` | Kontrol amaçlı önizleme görüntüleri |

## İçe aktarma
- **Birim:** metre · **Eksen:** Y-yukarı (OBJ ve GLB). Orijin: parselin güneybatı (arka-sol) köşesi.
- **Blender / 3ds Max / Lumion / Twinmotion / D5:** GLB veya OBJ doğrudan açılır. Malzemeler ada göre ayrık (`cam`, `cephe_beyaz`, `sagir_duvar`, `zemin_kat`…); render programında bu adlara kendi malzemelerini atayabilirsin.
- **SketchUp:** OBJ içe aktarırken "Swap YZ" (Y/Z değiştir) seçeneği gerekebilir; birim metre.
- Her kat ayrı nesne (`kat_1` … `kat_7`, `kat_n_balkon`, `kat_n_pencere` …) — kat bazında gizleme/seçme kolay.
- Yön: parselin uzun ekseni modelde X ekseni; gerçek kuzey modelde yaklaşık **12,9° sola (saat yönü tersine)** dönük. Güneş ayarını buna göre yap.

## Kütle ölçüleri
| | |
|---|---|
| Zemin kat | 80,8 × 11,5 m, h = 4,5 m (taban 929 m²) |
| Daire bloğu | 60,8 × 10 m, yol tarafına yaslı; 7 kat × 3,0 m |
| Bina yüksekliği | ±0,00'dan çatı döşemesine **25,5 m** (+1,2 m parapet, +2,7 m merdiven/asansör çıkışı) |
| Normal kat alanı | 608 m² × 7 = 4.256 m² |
| Toplam inşaat alanı (bodrum hariç) | ≈ 5.185 m² → **emsal ≈ 1,72** |
| Daire başı ortak alan payı | ≈ 45 m² (2 çekirdek + koridor) |
| Zemin kat çatısı (blok arkası, 20 × 11,5 m) | Ortak teras |

## Dikkat
- Bina 21,50 m'yi geçtiği için yangın yönetmeliğine göre **"yüksek bina"** sayılır: basınçlandırmalı yangın merdiveni, yangın asansörü vb. gerekir. İmar durumundaki Hmax / kat adedi kontrol edilmeli.
- Lobi B, yeni daire bloğunun çekirdeğinin altına gelecek şekilde 20 m yola doğru kaydırıldı (DK5 ile DK4 arası). Dükkan alanları değişmedi.
- Model `../gen/kutle.py` ile üretilir (`pip install trimesh numpy` → `python3 kutle.py`).
