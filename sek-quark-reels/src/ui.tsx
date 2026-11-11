import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { BRAND, C, F } from "./brand";

export const EXPO = Easing.bezier(0.16, 1, 0.3, 1);
export const INOUT = Easing.bezier(0.65, 0, 0.35, 1);

export const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** 0→1 arası, belirtilen karede başlayıp `dur` karede biten expo-out ilerleme. */
export const prog = (frame: number, start: number, dur = 14, ease = EXPO) =>
  interpolate(frame, [start, start + dur], [0, 1], { ...clamp, easing: ease });

/** Hafif zıplamalı yay animasyonu (pop-in için). */
export const usePop = (start: number, cfg?: { damping?: number; mass?: number; stiffness?: number }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({
    frame: frame - start,
    fps,
    config: { damping: 13, mass: 0.6, stiffness: 160, ...cfg },
  });
};

/** Satır satır yukarı kayarak beliren metin (maske içinde). */
export const RiseText: React.FC<{
  start: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
  dur?: number;
}> = ({ start, children, style, dur = 16 }) => {
  const frame = useCurrentFrame();
  const p = prog(frame, start, dur);
  return (
    <div style={{ overflow: "hidden", paddingBottom: "0.08em", marginBottom: "-0.08em" }}>
      <div
        style={{
          transform: `translateY(${(1 - p) * 105}%)`,
          opacity: p > 0 ? 1 : 0,
          ...style,
        }}
      >
        {children}
      </div>
    </div>
  );
};

/** Filmik grain dokusu: premium his için çok hafif, her 2 karede bir değişir. */
export const Grain: React.FC<{ opacity?: number }> = ({ opacity = 0.07 }) => {
  const frame = useCurrentFrame();
  const seed = Math.floor(frame / 2) % 50;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "overlay", opacity }}>
      <svg width="100%" height="100%">
        <filter id={`g${seed}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={seed} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#g${seed})`} />
      </svg>
    </AbsoluteFill>
  );
};

/** Sahne 2-4'te üstte duran, şeffaflık bildiren seri etiketi. */
export const TopBar: React.FC<{ dark?: boolean; start?: number }> = ({ dark = true, start = 0 }) => {
  const frame = useCurrentFrame();
  const p = prog(frame, start, 14);
  const fg = dark ? C.white : C.ink;
  return (
    <div
      style={{
        position: "absolute",
        top: 196,
        left: 72,
        right: 72,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        opacity: p,
        transform: `translateY(${(1 - p) * -20}px)`,
        fontFamily: F.body,
        fontWeight: 700,
        fontSize: 28,
        letterSpacing: 2,
        color: fg,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "10px 20px",
          borderRadius: 999,
          border: `2px solid ${dark ? "rgba(255,255,255,0.22)" : "rgba(13,16,20,0.18)"}`,
        }}
      >
        <div style={{ width: 12, height: 12, borderRadius: 6, background: C.lime, boxShadow: `0 0 12px ${C.lime}` }} />
        BAĞIMSIZ İNCELEME
      </div>
      <div style={{ opacity: 0.7 }}>{BRAND.name} · #01</div>
    </div>
  );
};

/** Sahneler arası geçiş: iki eğik bant (lime + hedef renk) ekranı süpürür. */
export const Wipe: React.FC<{ at: number; to: string; dir?: 1 | -1 }> = ({ at, to, dir = 1 }) => {
  const frame = useCurrentFrame();
  const span = 10;
  const lag = 3;
  if (frame < at - span - lag || frame > at + span + lag + 1) return null;
  const EIN = Easing.bezier(0.7, 0, 0.84, 0);
  // bant: aşağıdan gelir, ekranı kapatır, yukarı çıkar. Lime bant önden girer, arkadan çıkar.
  const band = (inA: number, outA: number) => {
    const pin = interpolate(frame, [inA - span, inA], [0, 1], { ...clamp, easing: EIN });
    const pout = interpolate(frame, [outA, outA + span], [0, 1], { ...clamp, easing: EXPO });
    return ((1 - pin) * 135 - pout * 135) * dir;
  };
  const style = (bg: string, y: number): React.CSSProperties => ({
    position: "absolute",
    left: "-25%",
    width: "150%",
    top: "-15%",
    height: "130%",
    background: bg,
    transform: `translateY(${y}%) skewY(-8deg)`,
  });
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={style(C.lime, band(at - lag, at + lag))} />
      <div style={style(to, band(at, at))} />
    </AbsoluteFill>
  );
};

/** Basit çizgi ikonlar (emoji yerine; her cihazda aynı görünür). */
export const Icon: React.FC<{ name: "target" | "clock" | "list" | "check" | "alert" | "plus"; size?: number; color?: string; stroke?: number }> = ({
  name,
  size = 64,
  color = C.ink,
  stroke = 5,
}) => {
  const common = { fill: "none", stroke: color, strokeWidth: stroke, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  return (
    <svg width={size} height={size} viewBox="0 0 64 64">
      {name === "target" && (
        <>
          <circle cx="32" cy="32" r="24" {...common} />
          <circle cx="32" cy="32" r="13" {...common} />
          <circle cx="32" cy="32" r="3" fill={color} />
        </>
      )}
      {name === "clock" && (
        <>
          <circle cx="32" cy="32" r="24" {...common} />
          <path d="M32 18 V32 L42 38" {...common} />
        </>
      )}
      {name === "list" && (
        <>
          <path d="M24 18 H50 M24 32 H50 M24 46 H42" {...common} />
          <circle cx="13" cy="18" r="3" fill={color} />
          <circle cx="13" cy="32" r="3" fill={color} />
          <circle cx="13" cy="46" r="3" fill={color} />
        </>
      )}
      {name === "check" && <path d="M14 33 L27 46 L51 19" {...common} />}
      {name === "alert" && (
        <>
          <path d="M32 8 L58 54 H6 Z" {...common} />
          <path d="M32 26 V38" {...common} />
          <circle cx="32" cy="46" r="2.5" fill={color} />
        </>
      )}
      {name === "plus" && <path d="M32 14 V50 M14 32 H50" {...common} />}
    </svg>
  );
};

/** Sayıyı yumuşakça sayarak gösterir (Türkçe ondalık). */
export const CountUp: React.FC<{ to: number; start: number; dur?: number; decimals?: number }> = ({
  to,
  start,
  dur = 26,
  decimals = 0,
}) => {
  const frame = useCurrentFrame();
  const v = interpolate(frame, [start, start + dur], [0, to], { ...clamp, easing: Easing.bezier(0.2, 0.7, 0.2, 1) });
  const s = decimals ? v.toFixed(decimals).replace(".", ",") : String(Math.round(v));
  return <span style={{ fontVariantNumeric: "tabular-nums" }}>{s}</span>;
};
