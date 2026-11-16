# Tasks & milestones

Status: [ ] todo · [~] in progress · [x] done (only when verified)

## M0 — Foundation
- [ ] Environment audit, Godot 4.7.1 installed, project skeleton
- [ ] CLAUDE.md, GAME_DESIGN.md, TASKS.md, RELEASE_CHECKLIST.md, 8 subagents
Acceptance: `godot --headless --path . --import` exits 0.

## M1 — Core rules (pure) + tests
- [ ] FruitCatalog, ScoreSystem, MergeResolver, DangerMonitor, DropQueue
Acceptance: unit tests pass headless.

## M2 — Playable loop
- [ ] Board, Fruit physics, dropper input, merging, scoring, game over, restart
Acceptance: headless physics integration test: merges happen once, no duplicate, game over triggers, restart clears.

## M3 — Persistence, settings, audio, haptics, localization
Acceptance: save/load + localization tests pass.

## M4 — UI/UX
- [ ] Menu, HUD, pause, settings, tutorial, game over; safe area; TR/EN
Acceptance: screenshots rendered under xvfb reviewed for both languages.

## M5 — Assets
- [ ] Fruits, icon, launch logo, sfx, music, font
Acceptance: all files in the contract exist and import cleanly.

## M6 — iOS release prep
- [ ] export_presets.cfg, Xcode project export attempt, docs, store metadata, privacy, screenshots, checklists
Acceptance: documented; anything requiring macOS/Apple account explicitly marked as NOT DONE.
