# Fruit Fusion — project guide

Original fruit-merging physics puzzle for iPhone. Godot 4.7.1 stable, GDScript only, portrait.
Primary UI language Turkish, English also shipped. Offline, no ads, no backend, no tracking in v1.

## Commands (run from `fruit-fusion/`)
- Import assets (needed after adding/changing assets or CSV): `godot --headless --path . --import`
- Run all tests: `godot --headless --fixed-fps 60 --path . res://tests/run_tests.tscn` (exit code 0 = pass)
- iOS Xcode project: `TEAM_ID=… BUNDLE_ID=… tools/export_ios_project.sh` (templates in `~/.local/share/godot/export_templates/4.7.1.stable/`)
- Regenerate art/audio: `python3 tools/gen_art.py && python3 tools/gen_audio.py`
- Store screenshots (needs xvfb): `tools/make_screenshots.sh`
- Godot binary in cloud sessions: `/usr/local/bin/godot` (not committed; download 4.7.1 from GitHub releases)

## Layout and ownership
| Path | Owner agent | Notes |
|---|---|---|
| `project.godot`, `src/core/`, `src/autoload/`, `CLAUDE.md`, `GAME_DESIGN.md`, `TASKS.md` | game-architect | contracts; pure logic |
| `src/game/game.gd`, `src/game/dropper.gd`, `src/main.gd`, `src/main.tscn` | gameplay-engineer | state machine, input, save/restore |
| `src/game/fruit.gd`, `src/game/board.gd`, physics settings | physics-engineer | bodies, walls, merge spawn stability |
| `src/ui/`, `localization/strings.csv` | ui-engineer | all screens, theme, safe area |
| `assets/`, `tools/gen_*.py` | asset-integrator | procedural original art + audio |
| `tests/`, `tools/make_screenshots.sh` | qa-engineer | headless tests |
| `export_presets.cfg`, `docs/ios/`, `RELEASE_CHECKLIST.md` | ios-release-engineer | export + Xcode procedure |
| `store/`, `docs/privacy/` | app-store-compliance | metadata, privacy, review |

Do not edit files owned by another agent; report the needed change to the orchestrator instead.

## Conventions
- Typed GDScript, tabs, `snake_case`; `class_name` for reusable classes.
- UI is built in code (no hand-authored complex `.tscn`); every visible string goes through `tr("KEY")`
  with keys in `localization/strings.csv` (columns `keys,en,tr`). Turkish must use proper characters (ş ğ ı İ ö ü ç).
- Pure rules live in `src/core/` (no scene tree access) so they are unit-testable.
- Never claim tests/builds passed unless actually run. Xcode/signing/App Store steps cannot be run here (Linux).
- Do not commit `.godot/`.

## Runtime contracts
Autoloads: `Settings`, `SaveData`, `AudioManager`, `Haptics`, `AdService` (see `src/autoload/`).

`Game` node (`src/game/game.gd`, class_name `Game`, a Node2D):
- signals: `score_changed(score:int)`, `best_changed(best:int)`, `next_fruit_changed(tier:int)`,
  `merged(tier:int, points:int, combo:int, pos:Vector2)`, `danger_changed(ratio:float)` (0..1),
  `game_over(score:int, is_new_best:bool)`, `state_changed(state:int)`
- enum `State { IDLE, PLAYING, PAUSED, GAME_OVER }`
- methods: `start_new_game()`, `resume_saved_game() -> bool`, `pause()`, `resume()`, `quit_to_menu()` (saves),
  `set_layout(play_rect: Rect2)`, `aim(x)`, `drop()`; properties `score:int`, `state:int`

Asset file names (all optional at runtime; code falls back to vector drawing / silence):
- `assets/fruits/fruit_01.png` … `fruit_11.png` — 512×512, transparent, fruit body is a circle touching all four edges
- `assets/audio/`: `sfx_drop.wav`, `sfx_merge.wav`, `sfx_fusion.wav`, `sfx_click.wav`, `sfx_warning.wav`,
  `sfx_gameover.wav`, `sfx_newbest.wav`, `music_loop.ogg`
- `assets/fonts/ui_font.ttf` (OFL, must cover Turkish), `assets/ui/jar_bg.png` optional backdrop
- `assets/icon/icon_1024.png` (no alpha), `assets/icon/launch_logo.png`

`UIRoot` (`src/ui/ui_root.gd`, CanvasLayer): `bind(game)`, `apply_layout(viewport_size, safe_top, safe_bottom)`. UI translation keys are prefixed `UI_`.
