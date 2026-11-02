"""index.html üretir:  python3 build.py"""
import os
from geom import *
from sheet_site import site_plan
from plans import ground_floor, typical_floor, unit_plan, flat_net

site_svg, n_surface = site_plan()
gf_area = (X1 - X0) * GF_DEPTH
shops = [(n, (b - a) * GF_DEPTH) for n, a, b in GF_MODULES if n.startswith("DK")]
shop_total = sum(a for _, a in shops)
lobby = sum((b - a) * GF_DEPTH for n, a, b in GF_MODULES if n.startswith("LOBI"))
tech = sum((b - a) * GF_DEPTH for n, a, b in GF_MODULES if n == "TEKNIK")
up_floor = (X1 - X0) * (Y_N - Y_UP_S)
flat_gross = FLAT_W * FLAT_D
balc = (BALCONY[2] - BALCONY[0]) * BALC_D
common_floor = up_floor - 7 * flat_gross
total = gf_area + 5 * up_floor
share = (common_floor * 5 + lobby) / 35
f = lambda v, d=0: f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

CSS = open(os.path.join(os.path.dirname(__file__), "style.css")).read()

rows = [
    ("Arsa alanı (4622/3)", f"≈ {f(PLOT_AREA)} m²", ""),
    ("Çekmeler sonrası yapılaşabilir zarf", f"≈ {f(poly_area(ENVELOPE))} m²", "yol 10 m · yanlar 3 m · arka 3 m (varsayım)"),
    ("Zemin kat taban alanı", f"{f(gf_area, 1)} m²", f"TAKS ≈ {gf_area / PLOT_AREA:.2f}".replace(".", ",")),
    ("&nbsp;&nbsp;• Ticari (7 dükkan)", f"<b>{f(shop_total, 1)} m²</b>", "6 × 115 m² + 1 × 80,5 m²"),
    ("&nbsp;&nbsp;• Konut girişleri (2 lobi + merdiven/asansör)", f"{f(lobby, 1)} m²", ""),
    ("&nbsp;&nbsp;• Teknik (çöp, elektrik, su sayaç)", f"{f(tech, 1)} m²", ""),
    ("Normal kat alanı (1.–5. kat, her biri)", f"{f(up_floor)} m²", f"+ balkonlar 7 × {f(balc, 1)} m²"),
    ("&nbsp;&nbsp;• 7 daire × 80 m² brüt", f"{f(7 * flat_gross)} m²", f"daire net ≈ {f(flat_net(), 1)} m²"),
    ("&nbsp;&nbsp;• Koridor + 2 çekirdek", f"{f(common_floor, 1)} m²", ""),
    ("Toplam inşaat alanı (bodrum hariç)", f"<b>≈ {f(total)} m²</b>", f"KAKS/Emsal ≈ {total / PLOT_AREA:.2f}".replace(".", ",")),
    ("Daire başı ortak alan payı", f"≈ {f(share)} m²", f"satış brütü ≈ {f(flat_gross + share)} m²"),
    ("Otopark", f"{n_surface} açık + ≈55–60 bodrum", "rampa %15, bodrumda sığınak + depolar"),
    ("Kat adedi / yükseklik", "Zemin + 5 kat", "≈ 4,5 + 5 × 3,0 = 19,5 m"),
]
table = "".join(f"<tr><td>{a}</td><td class='num'>{b}</td><td class='muted'>{c}</td></tr>" for a, b, c in rows)

html = f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>4622/3 Ön Proje</title><style>{CSS}</style></head><body>
<svg width="0" height="0" style="position:absolute"><defs>
<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs></svg>
<main>
<header><p class="eyebrow">Ada/Parsel 4622/3 · Ön (kütle) proje taslağı</p>
<h1>Zemin ticari + 35 daire (2+1) yerleşim önerisi</h1>
<p class="lead">Zemin katta <b>770 m² / 7 dükkan</b>, üstte <b>5 kat × 7 daire = 35 adet 2+1, balkonlu, ≈72 m² net</b>.
Bina kuzey çekme hattına oturtuldu; tüm daireler aynı ana cepheye (güney-güneybatı, açık taraf) ve yola doğru dönük.</p></header>

<section class="card callout"><h2>“Daireler öne baksın” konusu</h2>
<p>Çekmelerden sonra yola bakan yapılabilir cephe yalnızca <b>≈25 m</b>. Bu genişliğe kat başına en fazla 2–3 daire sığar; 7 dairenin hepsini doğrudan yola baktırmak fiziksel olarak mümkün değil. Önerilen çözüm:</p>
<ul>
<li><b>Tek yönlü koridor:</b> Koridor kuzey (komşu boş arsa) tarafında, <b>7 dairenin tamamı</b> güney-güneybatı ana cepheye bakıyor. Arka taraf/komşu cephesine bakan daire yok.</li>
<li>Her dairede <b>salon + balkon yol tarafındaki köşede</b>; Daire 7 köşe daire olup doğrudan caddeye de pencere alıyor.</li>
<li>Ana cephenin önünde 13,5 m kendi açık alanımız (araç yolu + otopark + yaya aksı) + 3 m bahçe var → güney komşuya ≥16 m mesafe, iyi gün ışığı.</li>
</ul>
<p class="muted">Bedeli: tek taraflı koridor ortak alanı artırır (daire başı ≈{f(share)} m²). Çift taraflı koridor daha verimli olur ama dairelerin yarısı arka/kuzeye bakar.</p></section>

<section class="card"><h2>1 · Vaziyet planı</h2><div class="sheet">{site_svg}</div>
<p class="cap">Bina parselin kuzey yan çekme hattına yaslı. Güneyde tek araç girişi, 6 m araç yolu, {n_surface} araçlık açık otopark ve bodrum rampası; dükkan önünde 4,5 m yaya aksı; yol tarafında ön meydan.</p></section>

<section class="card"><h2>2 · Zemin kat — 7 dükkan (770,5 m²)</h2><div class="sheet">{ground_floor()}</div>
<p class="cap">Dükkanlar 10 m vitrin × 11,5 m derinlik (115 m²); her birinde WC. DÜKKAN 1 köşe dükkan (cadde + yan vitrin). Ara duvarlar taşıyıcı olmadığından DÜKKAN 1+2 birleşip ≈230 m² market yapılabilir. Konut girişleri dükkan sırası arasında (A ve B), teknik hacimler arkada.</p></section>

<section class="card"><h2>3 · Normal kat (1.–5. kat) — kat başı 7 daire</h2><div class="sheet">{typical_floor()}</div>
<p class="cap">İki çekirdek (merdiven + asansör) kaçış mesafelerini sağlar; uç dairelerde çıkmaz koridor ≈5 m. Balkonlar zemin kat cephesine hizalı, dükkan önüne saçak oluşturur.</p></section>

<section class="card"><h2>4 · Tip daire — 2+1, ≈{f(flat_net(), 1)} m² net + {f(balc, 1)} m² balkon</h2><div class="sheet narrow">{unit_plan()}</div>
<p class="cap">10 × 8 m (80 m² brüt). Yatak odaları ve salon ana cepheye bakıyor; mutfak salona açık (Amerikan), banyo/WC/kiler iç hacimde şaftla havalandırılır.</p></section>

<section class="card"><h2>5 · Alan tablosu</h2><table>{table}</table></section>

<section class="card"><h2>6 · Varsayımlar ve kontrol edilmesi gerekenler</h2><ol>
<li>Ölçüler uydu görüntüsündeki kenar uzunluklarından (100 / 94,1 / 31,2 / 32,3 m) türetildi; kadastro/aplikasyon krokisiyle doğrulanmalı.</li>
<li>Arka bahçe mesafesi verilmediği için <b>3 m</b> alındı. İmar durumunda daha fazlaysa (ör. H/2) bina boyunda ≈2 m pay var; fazlası için daire genişliği 10 m → 9,6 m yapılabilir.</li>
<li><b>Emsal ≈ {total / PLOT_AREA:.2f}</b> ve <b>TAKS ≈ {gf_area / PLOT_AREA:.2f}</b> çıkıyor; imar durumundaki emsal/TAKS/Hmax ile karşılaştırılmalı (balkonların emsale dahil olup olmadığına dikkat).</li>
<li>Otopark ihtiyacı belediye otopark yönetmeliğine göre (genelde daire başı 1 + dükkanlar için ek) — ≈45–50 araç; açık + bodrum kapasitesi yeterli görünüyor.</li>
<li>Yangın yönetmeliği: 2 kaçış merdiveni, koridorda duman tahliyesi; bina yüksekliği 21,50 m altında (yüksek bina değil). Sığınak bodrumda.</li>
<li>Bu çizim kütle/fizibilite taslağıdır; ruhsat projesi mimar tarafından hazırlanmalıdır.</li>
</ol></section>
<footer class="muted"><a href="testere-disi.html">→ Varyant B: testere dişi cephe</a> · Çizimler ölçeklidir (vaziyet ≈1/1000, katlar ≈1/750, daire ≈1/200 ekranda). Kaynak: gen/ klasöründeki Python betikleri.</footer>
</main></body></html>"""
out = os.path.join(os.path.dirname(__file__), "..", "index.html")
open(out, "w").write(html)
print("yazıldı:", os.path.abspath(out), f"| toplam {total:.0f} m2, emsal {total/PLOT_AREA:.2f}, pay {share:.1f}")
