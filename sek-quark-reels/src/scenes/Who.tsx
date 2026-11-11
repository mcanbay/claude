import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { C, F } from "../brand";
import { clamp, Icon, prog, RiseText, TopBar, usePop } from "../ui";

const ITEMS: { icon: "target" | "clock" | "list"; title: string; sub: string; at: number }[] = [
  { icon: "target", title: "Protein alımını takip edenler", sub: "Paket başına ≈ 20 g protein", at: 30 },
  { icon: "clock", title: "Pratik ara öğün arayanlar", sub: "Kaşıkla, hazır tüketilir", at: 56 },
  { icon: "list", title: "Kısa içerik listesi sevenler", sub: "Süt + peynir kültürü", at: 82 },
];

/** SAHNE 4 (17-24 sn): Kimler için tercih edilebilir + dürüst uyarı. */
export const Who: React.FC = () => {
  const frame = useCurrentFrame();
  const warn = usePop(126, { damping: 14 });
  const listOut = interpolate(frame, [120, 134], [0, 1], clamp);

  return (
    <AbsoluteFill style={{ background: C.ink, overflow: "hidden" }}>
      <AbsoluteFill style={{ background: "radial-gradient(circle at 90% 20%, rgba(200,241,53,0.16), transparent 45%)" }} />
      {/* köşede küçük ürün hatırlatıcı */}
      <Img
        src={staticFile("cup.png")}
        style={{
          position: "absolute",
          width: 360,
          right: -90,
          top: 1180,
          transform: `rotate(${-16 + Math.sin(frame / 20) * 2}deg) translateY(${(1 - prog(frame, 6, 20)) * 300}px)`,
          opacity: 0.9,
          filter: "drop-shadow(0 30px 40px rgba(0,0,0,0.6))",
        }}
      />
      <TopBar start={4} />

      <div style={{ position: "absolute", top: 290, left: 72, right: 72, fontFamily: F.display, fontWeight: 800, fontSize: 84, letterSpacing: -3, lineHeight: 1.02, color: C.white }}>
        <RiseText start={4}>Kimler için</RiseText>
        <RiseText start={10}>
          <span style={{ color: C.lime }}>mantıklı</span> bir seçenek
        </RiseText>
        <RiseText start={16}>olabilir?</RiseText>
      </div>

      {ITEMS.map((it, i) => {
        const p = usePop(it.at);
        const dim = interpolate(listOut, [0, 1], [1, 0.55]);
        return (
          <div
            key={it.title}
            style={{
              position: "absolute",
              left: 72,
              right: 72,
              top: 640 + i * 170,
              display: "flex",
              alignItems: "center",
              gap: 30,
              transform: `translateX(${(1 - p) * -160}px)`,
              opacity: Math.min(1, p * 1.4) * dim,
              fontFamily: F.body,
            }}
          >
            <div style={{ flex: "0 0 auto", width: 120, height: 120, borderRadius: 34, background: C.lime, display: "flex", alignItems: "center", justifyContent: "center", transform: `rotate(${(1 - p) * -30}deg)` }}>
              <Icon name={it.icon} size={70} color={C.ink} stroke={5.5} />
            </div>
            <div>
              <div style={{ fontWeight: 800, fontSize: 48, color: C.white, lineHeight: 1.1 }}>{it.title}</div>
              <div style={{ fontWeight: 500, fontSize: 34, color: C.mutedDark, marginTop: 6 }}>{it.sub}</div>
            </div>
          </div>
        );
      })}

      {/* dürüst not */}
      <div
        style={{
          position: "absolute",
          left: 72,
          right: 72,
          top: 1150,
          padding: "30px 34px",
          borderRadius: 32,
          background: "#1B1F26",
          border: `3px solid ${C.warn}`,
          fontFamily: F.body,
          color: C.white,
          transform: `translateY(${(1 - warn) * 120}px)`,
          opacity: Math.min(1, warn * 1.5),
          boxShadow: "0 30px 60px rgba(0,0,0,0.45)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14, fontWeight: 800, fontSize: 32, letterSpacing: 3, color: C.warn }}>
          <Icon name="alert" size={40} color={C.warn} stroke={5} /> DİKKAT
        </div>
        <div style={{ fontWeight: 700, fontSize: 40, lineHeight: 1.25, marginTop: 10 }}>
          Süt ve laktoz içerir. Meyveli çeşitlerin değerleri farklı; içinde şeker olabilir.
        </div>
        <div style={{ fontWeight: 600, fontSize: 30, color: C.mutedDark, marginTop: 10 }}>Raftan alırken etiketi kontrol et.</div>
      </div>
    </AbsoluteFill>
  );
};
