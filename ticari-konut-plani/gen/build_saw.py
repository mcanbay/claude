"""testere-disi.html üretir:  python3 build_saw.py"""
import os
from geom import *
from sheet_site import site_plan
from plans import typical_floor, unit_plan, flat_net, saw_balc_area

here = os.path.dirname(os.path.abspath(__file__))
CSS = open(os.path.join(here, "style.css")).read()
site_svg, _ = site_plan(saw=True)
ang = round(SAW_ANGLE)
tip_gap = Y_UP_S - SAW_DEPTH - Y_GF_S

cmp_rows = [
    ("Balkon alanı", f"{(BALCONY[2]-BALCONY[0])*BALC_D:.1f} m²".replace(".", ","), f"{saw_balc_area():.1f} m²".replace(".", ",")),
    ("Balkonun baktığı yön", "Güney-güneybatı (cepheye dik)", f"Yola doğru ≈{ang}° döndürülmüş (güneydoğu)"),
    ("Yan komşu daireden görünürlük", "Balkonlar yan yana, açık", "Batı yanı sağır duvar → balkonlar birbirini görmez"),
    ("Daire net alanı", f"≈{flat_net():.1f} m²".replace(".", ","), "Aynı (iç plan değişmedi)"),
    ("Emsal etkisi", "—", "Aynı balkon alanı → değişmez"),
    ("Cephe çıkması", f"{BALC_D:.1f} m".replace(".", ","), f"Diş ucu {SAW_DEPTH:.1f} m (revak üstüne {abs(tip_gap):.1f} m taşar)".replace(".", ",")),
    ("Maliyet", "Standart konsol balkon", "Biraz daha fazla: açılı korkuluk + 7 sağır perde/kat"),
]
rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td><b>{c}</b></td></tr>" for a, b, c in cmp_rows)

html = f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Testere Dişi Cephe</title><style>{CSS}</style></head><body>
<svg width="0" height="0" style="position:absolute"><defs>
<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker><marker id="ahv" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#d9822b"/></marker></defs></svg>
<main>
<header><p class="eyebrow">Ada/Parsel 4622/3 · Varyant B</p>
<h1>Testere dişi cephe — balkonlar yola dönük</h1>
<p class="lead">Bina kütlesi, zemin kat dükkanları ve daire iç planları <a href="index.html">ana öneriyle</a> aynı. Değişen tek şey salon önündeki balkon:
dikdörtgen balkon yerine her dairede <b>üçgen bir “diş”</b> var. Dişin açık yüzü yola doğru <b>≈{ang}°</b> dönük, batı kenarı ise sağır bir mahremiyet duvarı.
Cepheye dışarıdan bakıldığında 35 balkon, yola doğru sıralanan testere dişleri gibi görünüyor.</p></header>

<section class="card callout"><h2>Nasıl çalışıyor?</h2><ul>
<li>Salon penceresi balkona açılıyor; balkonun camlı/korkuluklu yüzü güneydoğuya, yani <b>caddeye doğru</b> bakıyor (turuncu oklar).</li>
<li>Balkonun batı yanı dolu duvar: yandaki dairenin balkonu görünmüyor, rüzgâr kesiliyor.</li>
<li>Tam doğuya (yolun kendisine) dik bakış yok; bir sonraki dişin sağır duvarı bunu keser. Bakış <b>yola doğru çapraz</b> oluyor. Daire 7 köşe daire olduğu için yolu doğrudan görüyor.</li>
<li>Balkon alanı ({saw_balc_area():.1f} m²) eskisiyle aynı tutuldu; emsal ve daire alanları değişmiyor.</li>
</ul></section>

<section class="card"><h2>1 · Vaziyet planı (dişler yeşil)</h2><div class="sheet">{site_svg}</div></section>
<section class="card"><h2>2 · Normal kat (1.–5. kat) — testere dişi cephe</h2><div class="sheet">{typical_floor(saw=True)}</div>
<p class="cap">Kalın siyah çizgi: sağır mahremiyet duvarı · yeşil kesikli çizgi: açık yüz (korkuluk) · turuncu ok: bakış yönü.</p></section>
<section class="card"><h2>3 · Tip daire — testere dişi balkon</h2><div class="sheet narrow">{unit_plan(saw=True)}</div></section>
<section class="card"><h2>4 · Karşılaştırma</h2><table>
<tr><td></td><td class="muted">A · Düz balkon</td><td class="muted">B · Testere dişi</td></tr>{rows}</table></section>
<section class="card"><h2>Notlar</h2><ol>
<li>Diş ucu dükkan önü revakın üstüne {abs(tip_gap):.1f} m taşıyor; imar yönetmeliğindeki çıkma kurallarına (bahçeye en fazla 1,5 m vb.) göre kontrol edilmeli. Gerekirse diş derinliği 2,5 m'ye düşürülür, balkon ≈5,3 m² olur.</li>
<li>Daha güçlü yol bakışı istenirse açı artırılabilir (diş derinliği ↑) ama balkonlar daralır ve revak üstüne daha çok taşar.</li>
<li>Kütle/fizibilite taslağıdır; ruhsat projesi mimar tarafından hazırlanmalıdır.</li>
</ol></section>
</main></body></html>"""
open(os.path.join(here, "..", "testere-disi.html"), "w").write(html)
print("ok", ang, round(tip_gap, 2))
