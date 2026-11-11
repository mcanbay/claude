import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";
import { C } from "./brand";
import { Hook } from "./scenes/Hook";
import { Nutrition } from "./scenes/Nutrition";
import { Outro } from "./scenes/Outro";
import { Product } from "./scenes/Product";
import { Who } from "./scenes/Who";
import TL from "./timeline.json";
import { Grain, Wipe } from "./ui";

const S = TL.scenes;

export const Video: React.FC = () => (
  <AbsoluteFill style={{ background: C.ink }}>
    <Sequence from={S.hook.from} durationInFrames={S.hook.duration}>
      <Hook />
    </Sequence>
    <Sequence from={S.product.from} durationInFrames={S.product.duration}>
      <Product />
    </Sequence>
    <Sequence from={S.nutrition.from} durationInFrames={S.nutrition.duration}>
      <Nutrition />
    </Sequence>
    <Sequence from={S.who.from} durationInFrames={S.who.duration}>
      <Who />
    </Sequence>
    <Sequence from={S.outro.from} durationInFrames={S.outro.duration}>
      <Outro />
    </Sequence>

    {/* sahne geçişleri: kesmeler bantların arkasında gizlenir */}
    <Wipe at={S.product.from} to={C.ink} />
    <Wipe at={S.nutrition.from} to={C.paper} />
    <Wipe at={S.who.from} to={C.ink} />
    <Wipe at={S.outro.from} to={C.lime} />

    <Grain />
    <Audio src={staticFile("soundtrack.wav")} />
  </AbsoluteFill>
);
