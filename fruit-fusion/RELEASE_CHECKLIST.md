# Fruit Fusion — release checklist

Tags: **[DONE]** verified in this repository (Linux, Godot 4.7.1) · **[MAC]** needs macOS + Xcode ·
**[APPLE]** needs an Apple Developer Program account · **[HUMAN]** a decision or legal declaration only the owner can make.

Nothing below tagged MAC / APPLE / HUMAN has been done or tested. No Xcode build, signing, device run,
TestFlight upload or App Review has taken place.

## 1. Game
- [x] **[DONE]** Core loop, merging, scoring, combo, danger line, game over, restart, pause, save/continue
- [x] **[DONE]** Turkish + English UI, live language switch, tutorial, settings (sound / music / vibration)
- [x] **[DONE]** 18 automated headless tests pass: `godot --headless --fixed-fps 60 --path . res://tests/run_tests.tscn`
- [x] **[DONE]** Visual check of all screens via software-rendered screenshots (xvfb, OpenGL)
- [ ] **[MAC]** Play on real iPhones — follow `docs/ios/DEVICE_TEST_PLAN.md` (touch feel, safe area, haptics, audio
      interruptions, background/resume, 120 Hz, performance). Haptics, real safe-area insets and the Metal renderer
      have never run on a device.

## 2. Assets
- [x] **[DONE]** Original procedural art/audio (`tools/gen_art.py`, `tools/gen_audio.py`); font Baloo-family OFL with licence in `assets/fonts/`
- [x] **[DONE]** App icon 1024×1024 without alpha; launch screen colour + logo configured
- [ ] **[MAC]** Check icon and launch screen on device and in Xcode's asset catalog (no warnings)

## 3. Export
- [x] **[DONE]** `export_presets.cfg` (portrait, iPhone, min iOS 15.0 = Godot 4.7.1 template deployment target, no capabilities)
- [x] **[DONE]** Xcode project generation verified on Linux with a dummy team ID
      (`tools/export_ios_project.sh`): produced `FruitFusion.xcodeproj`, `.pck` without tests/tools/docs,
      portrait-only Info.plist, `ITSAppUsesNonExemptEncryption=false`, `PrivacyInfo.xcprivacy`, tr/en display name.
      Godot's own message: ".ipa can only be built on macOS".
- [ ] **[HUMAN]** Choose the final bundle identifier (placeholder: `com.example.fruitfusion`)
- [ ] **[APPLE]** Register the App ID; note the Team ID
- [ ] **[MAC]** `TEAM_ID=… BUNDLE_ID=… tools/export_ios_project.sh`, open in Xcode, automatic signing, build & run
- [ ] **[MAC]** Archive → Validate → Upload (see `docs/ios/BUILD_AND_RELEASE.md`); confirm Apple's current minimum Xcode/SDK

## 4. App Store Connect
- [ ] **[HUMAN]** Confirm the name is available / not infringing — see `store/NAME_OPTIONS.md`
- [ ] **[APPLE]** Create the app record; paste metadata from `store/metadata/{tr,en-US}/` (limits verified by script)
- [ ] **[HUMAN]** Host the privacy policy (`docs/privacy/`) and a support page; replace the placeholder URLs and contact details
- [ ] **[APPLE]** App Privacy answers per `store/APP_PRIVACY.md` (Data Not Collected), age rating per `store/AGE_RATING.md`,
      export compliance per `store/EXPORT_COMPLIANCE.md`
- [ ] **[APPLE]** Upload screenshots from `store/screenshots/{tr,en-US}/{1320x2868,1206x2622}/` (real gameplay, no captions;
      captions from `store/SCREENSHOT_PLAN.md` are optional and not rendered)
- [ ] **[HUMAN]** Pricing, territories, EU DSA trader status, content-rights declaration — `store/HUMAN_ACTIONS.md`

## 5. TestFlight and review
- [ ] **[APPLE]** `docs/ios/TESTFLIGHT_CHECKLIST.md`
- [ ] **[APPLE]** `store/APP_REVIEW_CHECKLIST.md`, review notes from `store/REVIEW_NOTES.md`, submit
