import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { C, F } from "../brand";
import { clamp, EXPO, prog, usePop } from "../ui";

/** SAHNE 1 (0-3 sn): Kaydırmayı durduran giriş. İlk karede bile ekran dolu. */
export const Hook: React.FC = () => {
  const frame = useCurrentFrame();

  // kamera: açılış "punch" + slam anında sarsıntı
  const punch = interpolate(frame, [0, 9], [1.07, 1], { ...clamp, easing: EXPO });
  const shakeAmt = interpolate(frame, [22, 32], [16, 0], clamp);
  const sx = Math.sin(frame * 2.7) * shakeAmt;
  const sy = Math.cos(frame * 3.3) * shakeAmt * 0.6;
  const drift = interpolate(frame, [0, 96], [0, 1]);

  const slam = usePop(22, { damping: 11, stiffness: 220, mass: 0.7 });
  const slamScale = interpolate(slam, [0, 1], [1.9, 1]);
  const cupIn = usePop(-4, { damping: 15, stiffness: 120 });

  const line = (start: number) => {
    const p = prog(frame, start, 10);
    return { opacity: p > 0 ? 1 : 0, transform: `translateY(${(1 - p) * 60}px)` };
  };

  const chips = [
    { t: "PROTEİN?", f: 56, x: 80, y: 1010, r: -4 },
    { t: "ŞEKER?", f: 62, x: 120, y: 1125, r: 3 },
    { t: "İÇİNDEKİLER?", f: 68, x: 70, y: 1240, r: -2 },
  ];

  return (
    <AbsoluteFill style={{ background: C.ink, overflow: "hidden" }}>
      {/* arka plan ışığı */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 75% 85%, rgba(200,241,53,0.22), transparent 55%), radial-gradient(circle at 10% 10%, rgba(61,123,255,0.18), transparent 50%)`,
        }}
      />
      {/* dev "kcal" kontur yazısı, yavaşça kayar */}
      <div
        style={{
          position: "absolute",
          top: 640,
          left: 60 - drift * 260,
          fontFamily: F.display,
          fontWeight: 800,
          fontSize: 560,
          color: "transparent",
          WebkitTextStroke: `3px rgba(200,241,53,0.16)`,
          letterSpacing: -20,
          whiteSpace: "nowrap",
        }}
      >
        kcal kcal
      </div>

      <AbsoluteFill style={{ transform: `scale(${punch}) translate(${sx}px, ${sy}px)` }}>
        {/* ürün: sağ alttan eğik girer */}
        <Img
          src={staticFile("cup.png")}
          style={{
            position: "absolute",
            width: 700,
            left: 430,
            top: 1150,
            transform: `translateY(${(1 - cupIn) * 520}px) rotate(${interpolate(cupIn, [0, 1], [28, 14]) + drift * 4}deg)`,
            filter: "drop-shadow(0 40px 60px rgba(0,0,0,0.6))",
          }}
        />

        <div style={{ position: "absolute", left: 72, top: 330, right: 60, fontFamily: F.display, color: C.white, fontWeight: 800 }}>
          <div style={{ fontSize: 104, lineHeight: 1.0, letterSpacing: -2, ...line(-7) }}>Yoğurt alırken</div>
          <div style={{ fontSize: 104, lineHeight: 1.0, letterSpacing: -2, marginTop: 6, ...line(10) }}>sadece</div>
          <div
            style={{
              display: "inline-block",
              marginTop: 20,
              fontSize: 146,
              lineHeight: 1,
              letterSpacing: -4,
              color: C.ink,
              background: C.lime,
              padding: "6px 22px 14px",
              borderRadius: 18,
              transform: `scale(${slamScale}) rotate(${interpolate(slam, [0, 1], [-8, -2])}deg)`,
              transformOrigin: "left center",
              opacity: frame >= 22 ? 1 : 0,
              boxShadow: "0 20px 60px rgba(200,241,53,0.35)",
            }}
          >
            KALORİSİNE
          </div>
          <div style={{ fontSize: 104, lineHeight: 1.0, letterSpacing: -2, marginTop: 26, ...line(46) }}>mi bakıyorsun?</div>
        </div>

        {/* "Etikette başka ne var?" çipleri */}
        {chips.map((c) => {
          const p = prog(frame, c.f, 12);
          return (
            <div
              key={c.t}
              style={{
                position: "absolute",
                left: c.x,
                top: c.y,
                transform: `translateX(${(1 - p) * -80}px) rotate(${c.r}deg) scale(${0.8 + 0.2 * p})`,
                opacity: p,
                fontFamily: F.body,
                fontWeight: 800,
                fontSize: 46,
                color: C.white,
                padding: "16px 30px",
                borderRadius: 999,
                border: `3px solid ${C.lime}`,
                background: "rgba(13,16,20,0.75)",
                letterSpacing: 1,
              }}
            >
              {c.t}
            </div>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
