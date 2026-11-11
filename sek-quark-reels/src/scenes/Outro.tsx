import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { BRAND, C, F } from "../brand";
import { clamp, EXPO, Icon, prog, RiseText, usePop } from "../ui";

/** SAHNE 5 (24-30 sn): Kapanış + takip çağrısı. */
export const Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const card = usePop(40, { damping: 14 });
  const tapAt = 70;
  const tapped = frame >= tapAt + 2;
  const press = interpolate(frame, [tapAt - 3, tapAt, tapAt + 5], [1, 0.9, 1], clamp);
  const cursorP = prog(frame, 50, 18);
  const ripple = interpolate(frame, [tapAt, tapAt + 18], [0, 1], { ...clamp, easing: EXPO });
  const morph = prog(frame, tapAt + 2, 10);
  const cta = prog(frame, 92, 14);
  const next = prog(frame, 108, 14);
  const zoom = interpolate(frame, [0, 180], [1, 1.04]);

  return (
    <AbsoluteFill style={{ background: C.lime, overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          backgroundImage: "radial-gradient(rgba(13,16,20,0.10) 3px, transparent 3px)",
          backgroundSize: "44px 44px",
          transform: `translateY(${frame * 0.5}px)`,
          height: "120%",
          top: "-10%",
        }}
      />
      <AbsoluteFill style={{ transform: `scale(${zoom})` }}>
        <div style={{ position: "absolute", top: 250, left: 72, right: 72, fontFamily: F.display, fontWeight: 800, fontSize: 110, letterSpacing: -4, lineHeight: 0.98, color: C.ink }}>
          <RiseText start={6}>Marketin</RiseText>
          <RiseText start={11}>sağlıklı tarafını</RiseText>
          <RiseText start={16}>
            <span style={{ background: C.ink, color: C.lime, padding: "0 18px", borderRadius: 16 }}>birlikte</span>
          </RiseText>
          <RiseText start={21}>keşfedelim.</RiseText>
        </div>

        {/* marka kartı + takip butonu */}
        <div
          style={{
            position: "absolute",
            left: 72,
            right: 72,
            top: 820,
            height: 300,
            borderRadius: 44,
            background: C.ink,
            padding: "40px 44px",
            boxSizing: "border-box",
            transform: `translateY(${(1 - card) * 200}px) scale(${0.9 + 0.1 * card})`,
            opacity: Math.min(1, card * 1.5),
            fontFamily: F.body,
            color: C.white,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 26 }}>
            <div style={{ width: 110, height: 110, borderRadius: 32, background: C.lime, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: F.display, fontWeight: 800, fontSize: 64, color: C.ink, letterSpacing: -3 }}>
              RA
            </div>
            <div>
              <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: 58, letterSpacing: -1 }}>{BRAND.name}</div>
              <div style={{ fontWeight: 500, fontSize: 32, color: C.mutedDark, marginTop: 2 }}>{BRAND.tagline}</div>
            </div>
          </div>
          {/* buton */}
          <div
            style={{
              position: "absolute",
              left: 44,
              right: 44,
              bottom: 36,
              height: 86,
              borderRadius: 999,
              background: interpolate(morph, [0, 1], [0, 1]) > 0.5 ? "rgba(255,255,255,0.1)" : C.lime,
              color: morph > 0.5 ? C.lime : C.ink,
              border: morph > 0.5 ? `3px solid ${C.lime}` : "3px solid transparent",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 12,
              fontWeight: 800,
              fontSize: 40,
              letterSpacing: 2,
              transform: `scale(${press})`,
              overflow: "hidden",
            }}
          >
            <Icon name={tapped ? "check" : "plus"} size={44} color={morph > 0.5 ? C.lime : C.ink} stroke={7} />
            {tapped ? "TAKİPTESİN" : "TAKİP ET"}
            <div
              style={{
                position: "absolute",
                left: "50%",
                top: "50%",
                width: 900,
                height: 900,
                marginLeft: -450,
                marginTop: -450,
                borderRadius: "50%",
                background: "rgba(255,255,255,0.35)",
                transform: `scale(${ripple})`,
                opacity: 1 - ripple,
              }}
            />
          </div>
        </div>

        {/* dokunan parmak imleci */}
        <div
          style={{
            position: "absolute",
            left: interpolate(cursorP, [0, 1], [900, 600]),
            top: interpolate(cursorP, [0, 1], [1400, 1060]) + (frame >= tapAt - 3 && frame < tapAt + 5 ? 8 : 0),
            width: 74,
            height: 74,
            borderRadius: 37,
            background: "rgba(255,255,255,0.92)",
            border: `5px solid ${C.ink}`,
            boxShadow: "0 10px 30px rgba(0,0,0,0.35)",
            opacity: cursorP * interpolate(frame, [tapAt + 10, tapAt + 22], [1, 0], clamp),
          }}
        />

        <div style={{ position: "absolute", left: 72, right: 72, top: 1160, fontFamily: F.body, color: C.ink, opacity: cta, transform: `translateY(${(1 - cta) * 30}px)` }}>
          <div style={{ fontWeight: 800, fontSize: 50, lineHeight: 1.15 }}>Daha fazla ürün incelemesi<br />için takip et!</div>
        </div>
        <div style={{ position: "absolute", left: 72, right: 72, top: 1300, fontFamily: F.body, color: C.ink, opacity: next, transform: `translateY(${(1 - next) * 30}px)`, fontWeight: 600, fontSize: 36 }}>
          Sıradaki ürünü yorumlarda sen seç ↓
        </div>
        <div style={{ position: "absolute", left: 72, right: 72, top: 1390, fontFamily: F.body, color: "rgba(13,16,20,0.62)", opacity: prog(frame, 20, 14), fontWeight: 600, fontSize: 26, lineHeight: 1.35 }}>
          Bağımsız inceleme · Sponsorlu değildir · Değerler 100 g içindir (Kasım 2026, Migros & Şok ürün sayfaları). Tıbbi tavsiye değildir.
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
