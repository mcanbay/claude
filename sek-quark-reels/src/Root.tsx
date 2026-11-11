import "@fontsource/bricolage-grotesque/500.css";
import "@fontsource/bricolage-grotesque/700.css";
import "@fontsource/bricolage-grotesque/800.css";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "@fontsource/inter/800.css";
import "@fontsource/inter/900.css";
import React from "react";
import { Composition, continueRender, delayRender, Still } from "remotion";
import { Cover } from "./Cover";
import TL from "./timeline.json";
import { Video } from "./Video";

// Türkçe karakterler (ğ, ş, İ, ı) latin-ext alt kümesinde; render başlamadan önce yüklenmelerini bekle.
const fontHandle = delayRender("fonts");
const SAMPLE = "ĞğŞşİıÇçÖöÜü 0123456789";
Promise.all(
  [
    "800 100px 'Bricolage Grotesque'",
    "700 100px 'Bricolage Grotesque'",
    "500 100px 'Bricolage Grotesque'",
    ...["400", "500", "600", "700", "800", "900"].map((w) => `${w} 100px 'Inter'`),
  ].map((f) => document.fonts.load(f, SAMPLE))
)
  .then(() => document.fonts.ready)
  .then(() => continueRender(fontHandle));

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="SekQuark" component={Video} durationInFrames={TL.durationInFrames} fps={TL.fps} width={TL.width} height={TL.height} />
    <Still id="Cover" component={Cover} width={1080} height={1920} />
  </>
);
