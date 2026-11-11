import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { C, F } from "../brand";
import { PRODUCT } from "../data";
import { clamp, prog, RiseText, TopBar, usePop } from "../ui";

/** SAHNE 2 (3-8 sn): Ürünün sinematik tanıtımı + "biliyor muydun" bilgisi. */
export const Product: React.FC = () => {
  const frame = useCurrentFrame();
  const enter = usePop(2, { damping: 16, stiffness: 90, mass: 0.9 });
  const float = Math.sin(frame / 18) * 10;
  const push = interpolate(frame, [0, 156], [1, 1.07]);
  const lightSweep = interpolate(frame, [30, 70], [-60, 160], clamp);
  const chip = usePop(96, { damping: 12 });

  return (
    <AbsoluteFill style={{ background: C.ink, overflow: "hidden" }}>
      {/* stüdyo ışığı */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse 70% 45% at 50% 46%, rgba(61,123,255,0.28), transparent 70%), radial-gradient(ellipse 60% 30% at 50% 78%, rgba(200,241,53,0.10), transparent 70%)`,
        }}
      />
      {/* dönen ince halka (odak) */}
      <div
        style={{
          position: "absolute",
          left: 540 - 430,
          top: 750 - 430,
          width: 860,
          height: 860,
          borderRadius: "50%",
          border: "2px solid rgba(255,255,255,0.08)",
          transform: `scale(${0.7 + enter * 0.3}) rotate(${frame * 0.4}deg)`,
          borderTopColor: "rgba(200,241,53,0.55)",
        }}
      />
      <TopBar start={6} />

      <div style={{ position: "absolute", top: 300, left: 72, right: 72, fontFamily: F.body, fontWeight: 600, fontSize: 52, lineHeight: 1.18, color: C.white }}>
        <RiseText start={6}>
          <span style={{ color: C.mutedDark }}>Bugün market rafından</span>
        </RiseText>
        <RiseText start={12}>farklı bir ürün seçtik:</RiseText>
      </div>

      {/* ürün */}
      <div
        style={{
          position: "absolute",
          left: 540 - 320,
          top: 430,
          width: 640,
          transform: `translateY(${(1 - enter) * 700 + float}px) rotate(${(1 - enter) * -14}deg) scale(${push * (0.75 + 0.25 * enter)})`,
        }}
      >
        <Img src={staticFile("cup.png")} style={{ width: 640, filter: "drop-shadow(0 50px 70px rgba(0,0,0,0.65))" }} />
        {/* parlama geçişi */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: `linear-gradient(105deg, transparent ${lightSweep - 12}%, rgba(255,255,255,0.28) ${lightSweep}%, transparent ${lightSweep + 12}%)`,
            WebkitMaskImage: `url(${staticFile("cup.png")})`,
            WebkitMaskSize: "100% 100%",
            mixBlendMode: "screen",
          }}
        />
      </div>
      {/* zemin gölgesi */}
      <div
        style={{
          position: "absolute",
          left: 540 - 300,
          top: 1035,
          width: 600,
          height: 60,
          borderRadius: "50%",
          background: "radial-gradient(closest-side, rgba(0,0,0,0.6), transparent)",
          opacity: enter,
          transform: `scaleX(${1 - float / 120})`,
        }}
      />

      {/* ürün adı */}
      <div style={{ position: "absolute", top: 1078, left: 72, right: 72, textAlign: "center", fontFamily: F.display, color: C.white }}>
        <RiseText start={38} style={{ fontSize: 40, fontFamily: F.body, fontWeight: 700, letterSpacing: 8, color: C.lime }}>
          {PRODUCT.brand}
        </RiseText>
        <RiseText start={42} style={{ fontSize: 116, fontWeight: 800, letterSpacing: -3, lineHeight: 1 }}>
          PROTEİN QUARK
        </RiseText>
        <div style={{ opacity: prog(frame, 52, 12), fontFamily: F.body, fontWeight: 600, fontSize: 40, color: C.mutedDark, marginTop: 10 }}>
          {PRODUCT.variant} · {PRODUCT.netG} g
        </div>
      </div>

      {/* biliyor muydun? */}
      <div
        style={{
          position: "absolute",
          left: 72,
          right: 72,
          top: 1318,
          padding: "22px 30px",
          borderRadius: 28,
          background: C.lime,
          color: C.ink,
          fontFamily: F.body,
          transform: `translateY(${(1 - chip) * 60}px) scale(${0.9 + 0.1 * chip})`,
          opacity: Math.min(1, chip * 1.5),
        }}
      >
        <div style={{ fontWeight: 800, fontSize: 28, letterSpacing: 3, opacity: 0.7 }}>BİLİYOR MUYDUN?</div>
        <div style={{ fontWeight: 700, fontSize: 40, lineHeight: 1.2, marginTop: 4 }}>
          Yoğurt gibi kaşıklanıyor ama quark aslında bir <b style={{ fontWeight: 900 }}>taze peynir</b> türü.
        </div>
      </div>
    </AbsoluteFill>
  );
};
