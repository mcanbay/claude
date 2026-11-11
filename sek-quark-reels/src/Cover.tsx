import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { BRAND, C, F } from "./brand";
import { Grain } from "./ui";

/** Reels/TikTok kapak görseli (1080x1920). Başlık 4:5 / 1:1 profil ızgarasında da okunur kalacak şekilde ortada. */
export const Cover: React.FC = () => (
  <AbsoluteFill style={{ background: C.ink, overflow: "hidden" }}>
    <AbsoluteFill style={{ background: "radial-gradient(circle at 70% 75%, rgba(200,241,53,0.25), transparent 55%), radial-gradient(circle at 15% 20%, rgba(61,123,255,0.2), transparent 50%)" }} />
    <div style={{ position: "absolute", top: 420, left: 72, right: 72, fontFamily: F.display, fontWeight: 800, color: C.white, letterSpacing: -3 }}>
      <div style={{ fontFamily: F.body, fontSize: 34, letterSpacing: 4, color: C.lime, marginBottom: 24 }}>{BRAND.episode}</div>
      <div style={{ fontSize: 92, lineHeight: 1.0 }}>Market rafında gördüğümüz bu yoğurt</div>
      <div style={{ display: "inline-block", fontSize: 120, lineHeight: 1, marginTop: 22, background: C.lime, color: C.ink, padding: "4px 22px 14px", borderRadius: 18, transform: "rotate(-2deg)" }}>
        gerçekten
      </div>
      <div style={{ fontSize: 120, lineHeight: 1.0, marginTop: 10 }}>sağlıklı mı?</div>
    </div>
    <Img src={staticFile("cup.png")} style={{ position: "absolute", width: 640, left: 400, top: 1080, transform: "rotate(12deg)", filter: "drop-shadow(0 40px 60px rgba(0,0,0,0.6))" }} />
    <div style={{ position: "absolute", left: 72, top: 1200, fontFamily: F.body, fontWeight: 800, fontSize: 44, color: C.white, lineHeight: 1.25 }}>
      Etiketi<br />birlikte<br />okuyoruz →
    </div>
    <Grain />
  </AbsoluteFill>
);
