# Tasks & milestones

Status: [x] done and verified here · [ ] not done (needs Mac / Apple account / human)

## M0 — Foundation [x]
Godot 4.7.1 installed, project skeleton, docs, 8 subagents in `.claude/agents/`.

## M1 — Core rules + tests [x]
FruitCatalog, ScoreSystem, MergeResolver, DangerMonitor, DropQueue, JsonFile.

## M2 — Playable loop [x]
Board, Fruit physics, drop input, deterministic merging, scoring, game over, restart.

## M3 — Persistence, settings, audio, haptics, localization [x]
Haptics code path is untested (no device).

## M4 — UI/UX [x]
Menu, HUD, pause, settings, tutorial, game over; safe-area layout; TR/EN. Checked via rendered screenshots.

## M5 — Assets [x]
11 fruits, icon, launch logo, backdrop, 7 SFX, 40 s music loop, OFL font.

## M6 — iOS release prep [x] in repo / [ ] outside
- [x] Export preset, Xcode project generated on Linux (dummy team ID), docs, metadata, privacy, screenshots, checklists
- [ ] Everything tagged MAC / APPLE / HUMAN in `RELEASE_CHECKLIST.md`

## Verification log
- 18/18 headless tests pass (Godot 4.7.1, Linux).
- Not run: Xcode build, signing, device or simulator run, TestFlight, App Review.

## Known gaps / ideas
- Screenshot captions are not rendered onto the images.
- Static resource caches report "resources still in use at exit" in headless runs (harmless).
- Rewarded-ad "continue" is only an `AdService` stub; no UI entry point yet.
