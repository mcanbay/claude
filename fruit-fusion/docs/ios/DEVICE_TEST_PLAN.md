# Device test plan — Fruit Fusion (iOS)

Manual test matrix for physical iPhones. Requires a Mac + Xcode (or a TestFlight build). Not executed
yet — record results per build in the table at the bottom. Minimum supported: iOS 15.0, A12 or newer
(Godot 4.7.1 mobile renderer adds the `iphone-ipad-minimum-performance-a12` requirement).

## Devices

| ID | Class | Example models | Why |
|---|---|---|---|
| D1 | Small, home button, 4.7" | iPhone SE (2nd/3rd gen) | Narrowest layout, no safe-area insets at top, Touch ID |
| D2 | Notch | iPhone XR / 11 / 12 / 13 | Top notch inset + home indicator |
| D3 | Dynamic Island, 60 Hz | iPhone 14 Pro is 120 Hz; use iPhone 15 / 16 | Dynamic Island inset |
| D4 | Dynamic Island, 120 Hz ProMotion | iPhone 14 Pro / 15 Pro / 16 Pro / 17 Pro | High refresh rate, physics interpolation |
| D5 | Large | any Pro Max / Plus | Widest layout |
| D6 | Oldest supported OS | any A12+ device on iOS 15.x or the oldest available | Min-OS compatibility |

At minimum: D1 + one of D2/D3 + D4. Simulators may complement but not replace real devices
(haptics, mute switch, 120 Hz, performance).

## Test cases

### Smoke
| # | Steps | Expected |
|---|---|---|
| S1 | Fresh install, launch | Launch screen with #FDF2DE background + logo, no white flash; main menu appears; tutorial on first run |
| S2 | Play a full game to game over | Drops, merges, score, combo, danger warning, game over screen work; no crash |
| S3 | Home screen icon and name | Icon correct (no black/transparent corners artefacts), name "Fruit Fusion" not truncated |

### Layout / safe area
| # | Steps | Expected |
|---|---|---|
| L1 | Each device: menu, HUD, pause, settings, tutorial, game over | No UI under the notch/Dynamic Island or home indicator; nothing clipped on D1 |
| L2 | Rotate device | App stays portrait (portrait only) |
| L3 | Status bar | Hidden (template sets `UIStatusBarHidden`) |
| L4 | Swipe from bottom edge during drag-aim | Aiming not broken by home-indicator gesture; app not accidentally closed in one swipe more than expected |

### Interruptions and lifecycle
| # | Steps | Expected |
|---|---|---|
| I1 | Incoming phone/FaceTime call mid-game (decline and accept) | Game pauses; audio stops; after call, pause screen shown, resume works |
| I2 | Pull down Notification Center / Control Center mid-game | Game pauses (focus lost) |
| I3 | Home → wait 10 s → reopen | Paused state restored, score intact |
| I4 | Home → kill app from app switcher → relaunch | Menu offers "Continue"; resumed run matches pre-kill board/score/next fruit |
| I5 | Lock screen mid-game, unlock | Paused, no audio playing while locked |
| I6 | Alarm / timer fires mid-game | Same as I1 |
| I7 | Low-memory: open many heavy apps, return | App either resumes or relaunches with Continue available; best score never lost |

### Audio / haptics
| # | Steps | Expected |
|---|---|---|
| A1 | Mute (Ring/Silent) switch or Action Button silent mode ON | Decide and verify intended behaviour (game audio normally respects silent mode); document result |
| A2 | Settings: sound off / music off | Respectively silent |
| A3 | Play Spotify/Music in background, launch game | Background music behaviour acceptable (no crash; document whether it is ducked/stopped) |
| A4 | Haptics ON: merge, fusion burst, danger, game over | Light/medium/heavy feedback felt |
| A5 | Haptics OFF in settings | No haptics |
| A6 | System haptics disabled (Settings → Sounds & Haptics) | No crash; no haptics |
| A7 | Bluetooth headphones connect/disconnect mid-game | Audio routes correctly, no crash |

### Performance / power
| # | Steps | Expected |
|---|---|---|
| P1 | D4 120 Hz: drop many fruits | Smooth motion (interpolation), no jitter; note FPS (Xcode Debug Navigator) |
| P2 | Low Power Mode ON | Game runs (likely 60 Hz cap), physics speed unchanged, no glitches |
| P3 | 15 min continuous play | No significant heat/throttling stutter; memory stable in Xcode gauges |
| P4 | Cold launch time | Under ~3 s to menu on D1 |

### Accessibility
| # | Steps | Expected |
|---|---|---|
| X1 | VoiceOver ON, launch | App launches; note that Godot UI is not exposed to VoiceOver by default — document what is read; ensure no trap (triple-click toggle still works) |
| X2 | Larger Text / Bold Text | No crash (Godot ignores Dynamic Type) |
| X3 | Reduce Motion | No crash; note whether effects respect it |

### Localization
| # | Steps | Expected |
|---|---|---|
| T1 | Device language Turkish | UI in Turkish with correct ş ğ ı İ ö ü ç glyphs; no missing glyph boxes |
| T2 | Device language English | UI in English |
| T3 | Device language other (e.g. German) | Falls back to English |
| T4 | Change language in in-game settings | Switches immediately, persists across relaunch |

### Data
| # | Steps | Expected |
|---|---|---|
| D-1 | Get a best score, relaunch | Best kept |
| D-2 | Update install (install build N then N+1 over it) | Best score and saved run preserved |
| D-3 | Airplane mode | Fully functional (offline game) |

## Results log

| Build | Device | iOS | Tester | Date | Failed cases / notes |
|---|---|---|---|---|---|
| | | | | | |
