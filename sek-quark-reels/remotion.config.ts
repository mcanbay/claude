import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setJpegQuality(95);
Config.setCodec("h264");
Config.setCrf(16);
Config.setPixelFormat("yuv420p");
// Ortamda önceden kurulu headless Chromium kullanılır (indirme gerekmez).
const chrome = process.env.REMOTION_CHROME;
if (chrome) Config.setBrowserExecutable(chrome);
