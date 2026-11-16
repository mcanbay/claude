# Screenshot plan

## Required sizes (App Store Connect, checked 2026-11-16 against Apple's "Screenshot specifications" page)

The app is iPhone-only (`application/targeted_device_family=0` in `export_presets.cfg`), so no iPad screenshots are
required. Portrait PNG or JPEG, RGB, **no alpha/transparency**, 1–10 per size per locale.

| Slot | Accepted portrait pixels | Status | We render |
|---|---|---|---|
| iPhone 6.9" "Dynamic Island (large)" | 1320×2868, 1290×2796, 1260×2736 | optional, but satisfies the large-phone requirement | **1320×2868** |
| iPhone 6.5" "Face ID (large)" | 1284×2778, 1242×2688 | required only if no Dynamic Island (large) set is uploaded | not needed |
| iPhone 6.3" "Dynamic Island (medium)" | 1206×2622, 1179×2556 | **required (at least one)** | **1206×2622** |
| iPhone Duo (foldable, outer/inner) | 1398×2034 / 2007×2853 | optional now; Apple says required for apps built with the iOS 27.1 SDK or later from April 2027 | not for v1 |

Smaller sizes are scaled down by Apple. The human must confirm the current list in App Store Connect at upload time,
as Apple changes it.

Output layout (rendered by the orchestrator / `tools/make_screenshots.sh`):
```
store/screenshots/tr/1320x2868/01_hero.png … 05_offline.png
store/screenshots/tr/1206x2622/...
store/screenshots/en-US/1320x2868/...
store/screenshots/en-US/1206x2622/...
```
Turkish is the primary locale: produce TR first; EN uses the English UI (`Settings` language = en).

## Shots and captions

Captions are a short headline at the top (≤ ~28 characters so they fit on one or two lines at a large font).
Screenshots must show **real gameplay from the actual build** (2.3.3); captions/frames are allowed, but no features that
do not exist, no other games' names, no "No.1/best" claims, no ratings/awards, no prices.

| # | Scene to capture | EN caption | TR caption |
|---|---|---|---|
| 1 | Mid-game jar, many tiers visible, merge particles | Drop. Merge. Grow! | Bırak. Birleştir. Büyüt! |
| 2 | A chain merge with combo label (×2 / ×3) | Chain combos for big points | Zincirleme kombo, dev puan |
| 3 | Ladder of fruits (blueberry → dragon fruit), e.g. tutorial or a composed in-game moment | 11 fruits to discover | Keşfedilecek 11 meyve |
| 4 | Danger line pulsing, pile near the rim | Keep it under the rim | Çizgiyi aşma! |
| 5 | Main menu with best score / Continue | Play offline, no ads | İnternetsiz oyna, reklam yok |
| 6 (opt.) | Game-over with new best | Beat your own record | Kendi rekorunu kır |

Notes:
- "no ads" in caption 5 must be removed the moment ads are added.
- Show the device language consistently: TR screenshots with Turkish UI, EN with English UI.
- Avoid showing the iOS status bar with a fake carrier/time; the game runs full-screen, so render without status bar.
- App preview video: optional, not planned for v1.
