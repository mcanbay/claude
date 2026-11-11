import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { C, F } from "../brand";
import { perPack, PRODUCT, tr } from "../data";
import { clamp, CountUp, EXPO, Icon, prog, RiseText, TopBar, usePop } from "../ui";

const P = PRODUCT.per100;

/** Alt panel kaydırma: sağdan girer, sola çıkar. */
const usePanel = (inAt: number, outAt: number | null) => {
  const frame = useCurrentFrame();
  const pin = inAt <= 0 ? 1 : interpolate(frame, [inAt, inAt + 14], [0, 1], { ...clamp, easing: EXPO });
  const pout = outAt == null ? 0 : interpolate(frame, [outAt, outAt + 12], [0, 1], { ...clamp, easing: Easing.bezier(0.7, 0, 0.84, 0) });
  const visible = frame >= inAt - 1 && (outAt == null || frame <= outAt + 13);
  return {
    visible,
    style: {
      transform: `translateX(${(1 - pin) * 1080 - pout * 1080}px)`,
    } as React.CSSProperties,
  };
};

const Title: React.FC<{ start: number; children: React.ReactNode; sub?: string }> = ({ start, children, sub }) => {
  const frame = useCurrentFrame();
  return (
    <div style={{ position: "absolute", top: 290, left: 72, right: 72 }}>
      <RiseText start={start} style={{ fontFamily: F.display, fontWeight: 800, fontSize: 92, letterSpacing: -3, color: C.ink, lineHeight: 1 }}>
        {children}
      </RiseText>
      <div style={{ height: 10, width: 220 * prog(frame, start + 6, 14), background: C.lime, borderRadius: 5, marginTop: 14 }} />
      {sub && (
        <div style={{ position: "absolute", right: 0, top: 112, opacity: prog(frame, start + 8, 10), fontFamily: F.body, fontWeight: 800, fontSize: 34, color: C.ink, background: C.lime, padding: "10px 22px", borderRadius: 999 }}>
          {sub}
        </div>
      )}
    </div>
  );
};

const SmallCard: React.FC<{ start: number; label: string; value: number; unit: string; decimals?: number; note?: string; x: number }> = ({
  start,
  label,
  value,
  unit,
  decimals = 0,
  note,
  x,
}) => {
  const pop = usePop(start);
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: 905,
        width: 296,
        height: 300,
        borderRadius: 34,
        background: C.white,
        boxShadow: "0 18px 40px rgba(13,16,20,0.10)",
        padding: "30px 26px",
        boxSizing: "border-box",
        transform: `translateY(${(1 - pop) * 80}px) scale(${0.85 + 0.15 * pop})`,
        opacity: Math.min(1, pop * 1.4),
        fontFamily: F.body,
        color: C.ink,
      }}
    >
      <div style={{ fontWeight: 800, fontSize: 30, letterSpacing: 2, color: C.muted }}>{label}</div>
      <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: 104, letterSpacing: -4, lineHeight: 1.05, marginTop: 14 }}>
        <CountUp to={value} start={start} dur={18} decimals={decimals} />
        <span style={{ fontSize: 44, letterSpacing: 0, marginLeft: 6 }}>{unit}</span>
      </div>
      {note && <div style={{ fontWeight: 600, fontSize: 28, color: C.muted, marginTop: 8 }}>{note}</div>}
    </div>
  );
};

/** SAHNE 3 (8-17 sn): Etiket analizi. */
export const Nutrition: React.FC = () => {
  const frame = useCurrentFrame();
  const A = usePanel(0, 144);
  const B = usePanel(144, 204);
  const Cc = usePanel(204, null);

  const hero = usePop(10, { damping: 15 });
  const heroBar = prog(frame, 12, 30);

  const chip1 = usePop(164);
  const chip2 = usePop(176);
  const noSugar = prog(frame, 186, 12);

  const badge = usePop(212, { damping: 14 });
  const eq = prog(frame, 228, 12);
  const stamp = usePop(250, { damping: 9, stiffness: 240 });

  return (
    <AbsoluteFill style={{ background: C.paper, overflow: "hidden" }}>
      {/* ince ızgara deseni */}
      <AbsoluteFill
        style={{
          backgroundImage: "linear-gradient(rgba(13,16,20,0.045) 2px, transparent 2px), linear-gradient(90deg, rgba(13,16,20,0.045) 2px, transparent 2px)",
          backgroundSize: "90px 90px",
          transform: `translateY(${-frame * 0.6}px)`,
          height: "130%",
        }}
      />
      <TopBar dark={false} start={4} />

      {/* ---------------- A: makrolar ---------------- */}
      {A.visible && (
        <AbsoluteFill style={A.style}>
          <Title start={4} sub="100 g'da">
            ETİKETİ OKUYALIM
          </Title>
          {/* protein kahraman kartı */}
          <div
            style={{
              position: "absolute",
              left: 72,
              right: 72,
              top: 480,
              height: 390,
              borderRadius: 44,
              background: C.ink,
              color: C.white,
              padding: "40px 48px",
              boxSizing: "border-box",
              transform: `translateY(${(1 - hero) * 120}px) scale(${0.9 + 0.1 * hero})`,
              opacity: Math.min(1, hero * 1.4),
              overflow: "hidden",
              fontFamily: F.body,
            }}
          >
            <div style={{ position: "absolute", right: -80, top: -80, width: 380, height: 380, borderRadius: "50%", background: "radial-gradient(closest-side, rgba(200,241,53,0.35), transparent)" }} />
            <div style={{ fontWeight: 800, fontSize: 34, letterSpacing: 4, color: C.lime }}>PROTEİN</div>
            <div style={{ display: "flex", alignItems: "baseline", fontFamily: F.display, fontWeight: 800, letterSpacing: -8, lineHeight: 1, marginTop: 6 }}>
              <span style={{ fontSize: 210, color: C.lime }}>
                <CountUp to={P.protein} start={12} dur={28} />
              </span>
              <span style={{ fontSize: 90, marginLeft: 12, letterSpacing: 0 }}>g</span>
            </div>
            {/* 100 g'ın ne kadarı protein */}
            <div style={{ position: "absolute", left: 48, right: 48, bottom: 44 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 600, fontSize: 30, color: C.mutedDark, marginBottom: 12 }}>
                <span>Her 100 g ürünün</span>
                <span style={{ color: C.white, fontWeight: 800 }}>{Math.round(P.protein * heroBar)} g'ı protein</span>
              </div>
              <div style={{ height: 22, borderRadius: 11, background: "rgba(255,255,255,0.12)", overflow: "hidden" }}>
                <div style={{ height: "100%", width: `${P.protein * heroBar}%`, background: C.lime, borderRadius: 11, boxShadow: `0 0 20px ${C.lime}` }} />
              </div>
            </div>
          </div>
          <SmallCard start={60} x={72} label="KALORİ" value={P.kcal} unit="kcal" />
          <SmallCard start={72} x={392} label="ŞEKER" value={P.sugar} unit="g" decimals={1} />
          <SmallCard start={84} x={712} label="YAĞ" value={P.fat} unit="g" note={`Doymuş: ${tr(P.satFat)} g`} />
          <div style={{ position: "absolute", left: 72, right: 72, top: 1240, opacity: prog(frame, 96, 12), fontFamily: F.body, fontWeight: 600, fontSize: 30, color: C.muted, lineHeight: 1.35 }}>
            Karbonhidrat {tr(P.carb)} g · Tuz {tr(P.salt)} g
            <br />
            Kaynak: ürün etiket bilgisi (Migros, Şok ürün sayfaları)
          </div>
        </AbsoluteFill>
      )}

      {/* ---------------- B: içindekiler ---------------- */}
      {B.visible && (
        <AbsoluteFill style={B.style}>
          <Title start={150}>İÇİNDEKİLER</Title>
          <div style={{ position: "absolute", left: 72, top: 470, display: "flex", alignItems: "flex-end", gap: 26, fontFamily: F.display, color: C.ink }}>
            <div style={{ fontSize: 330, fontWeight: 800, lineHeight: 0.8, letterSpacing: -10, color: C.ink }}>2</div>
            <div style={{ fontSize: 76, fontWeight: 800, lineHeight: 1, paddingBottom: 6, letterSpacing: -2 }}>
              bileşen.
              <div style={{ fontFamily: F.body, fontSize: 36, fontWeight: 600, color: C.muted, letterSpacing: 0, marginTop: 10 }}>Hepsi bu kadar.</div>
            </div>
          </div>
          {[
            { t: PRODUCT.ingredients[0], p: chip1, n: "1" },
            { t: PRODUCT.ingredients[1], p: chip2, n: "2" },
          ].map((c, i) => (
            <div
              key={c.t}
              style={{
                position: "absolute",
                left: 72,
                right: 72,
                top: 830 + i * 150,
                height: 124,
                display: "flex",
                alignItems: "center",
                gap: 26,
                padding: "0 34px",
                borderRadius: 30,
                background: C.white,
                boxShadow: "0 14px 34px rgba(13,16,20,0.08)",
                transform: `translateX(${(1 - c.p) * 200}px)`,
                opacity: Math.min(1, c.p * 1.4),
                fontFamily: F.body,
              }}
            >
              <div style={{ width: 64, height: 64, borderRadius: 32, background: C.lime, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, fontSize: 34 }}>{c.n}</div>
              <div style={{ fontWeight: 700, fontSize: 50, color: C.ink }}>{c.t}</div>
            </div>
          ))}
          <div
            style={{
              position: "absolute",
              left: 72,
              top: 1150,
              display: "flex",
              alignItems: "center",
              gap: 18,
              opacity: noSugar,
              transform: `translateY(${(1 - noSugar) * 30}px)`,
              fontFamily: F.body,
              fontWeight: 800,
              fontSize: 44,
              color: C.ink,
            }}
          >
            <div style={{ width: 70, height: 70, borderRadius: 35, background: C.ink, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Icon name="check" size={46} color={C.lime} stroke={7} />
            </div>
            Listede ilave şeker yok.
          </div>
        </AbsoluteFill>
      )}

      {/* ---------------- C: kapaktaki iddia ---------------- */}
      {Cc.visible && (
        <AbsoluteFill style={Cc.style}>
          <Title start={210}>KAPAKTA YAZAN</Title>
          <div
            style={{
              position: "absolute",
              left: 540 - 300,
              top: 470,
              width: 600,
              height: 349,
              borderRadius: 40,
              overflow: "hidden",
              boxShadow: "0 30px 60px rgba(13,16,20,0.25)",
              transform: `scale(${0.6 + 0.4 * badge}) rotate(${(1 - badge) * 8 - 3}deg)`,
              opacity: Math.min(1, badge * 1.5),
            }}
          >
            <Img src={staticFile("badge.png")} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${1 + frame * 0.0008})` }} />
          </div>
          <div style={{ position: "absolute", left: 72, right: 72, top: 870, textAlign: "center", opacity: eq, transform: `translateY(${(1 - eq) * 30}px)`, fontFamily: F.body, color: C.ink }}>
            <div style={{ fontWeight: 600, fontSize: 40, color: C.muted }}>Etiketle sağlamasını yapalım:</div>
            <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: 64, letterSpacing: -1, marginTop: 18, lineHeight: 1.15 }}>
              100 g'da {P.protein} g ise {PRODUCT.netG} g'lık pakette
            </div>
            <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: 150, letterSpacing: -5, lineHeight: 1.1 }}>
              = <CountUp to={perPack(P.protein)} start={234} dur={16} decimals={1} /> g
            </div>
          </div>
          <div
            style={{
              position: "absolute",
              left: 540 - 300,
              top: 1330,
              width: 600,
              height: 110,
              borderRadius: 999,
              background: C.ink,
              color: C.lime,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 16,
              fontFamily: F.body,
              fontWeight: 800,
              fontSize: 44,
              transform: `scale(${interpolate(stamp, [0, 1], [1.6, 1])}) rotate(-2deg)`,
              opacity: Math.min(1, stamp * 2),
            }}
          >
            <Icon name="check" size={52} color={C.lime} stroke={8} />
            Etiketle tutarlı
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
