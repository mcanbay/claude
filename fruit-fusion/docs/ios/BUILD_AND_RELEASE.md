# Fruit Fusion — iOS build and release

Engine: Godot 4.7.1 stable. Target: iPhone only, portrait only. Preset: `export_presets.cfg` → `[preset.0]` "iOS".

Status legend used throughout: **verified on Linux** = actually run in the cloud container;
**not verified** = must be done by a human on a Mac / with an Apple Developer account. Nothing in the
Xcode, signing, device, upload or TestFlight sections below has been run or verified yet.

---

## 1. Facts verified from the real Godot 4.7.1 export template

Checked against the official `ios.zip` from the 4.7.1-stable export templates and the 4.7.1-stable
sources (`platform/ios/export/export_plugin.{h,cpp}`, `editor/export/editor_export_platform_apple_embedded.cpp`):

| Item | Value | Where it comes from |
|---|---|---|
| Minimum iOS deployment target | **15.0** | `export_plugin.h`: `get_minimum_deployment_target() { return "15.0"; }`; default of option `application/min_ios_version`. The template's `project.pbxproj` contains only a `$os_deployment_target` placeholder; the exported project contains `IPHONEOS_DEPLOYMENT_TARGET = 15.0;` (verified on Linux, see §4). |
| Device requirement | `UIRequiredDeviceCapabilities = iphone-ipad-minimum-performance-a12` is **always added** when the renderer is `mobile` or `forward_plus` (our project uses `mobile`). So the build only installs on **A12 or newer** iPhones (iPhone XS / XR and later), even though iOS 15 itself runs on older phones. Switching `rendering/renderer/rendering_method` to `gl_compatibility` would remove this — a [HUMAN-DECISION], not done. |
| Architectures | `arm64` only (device). Simulator slices exist in the template xcframeworks. |
| `ITSAppUsesNonExemptEncryption` | Already hard-coded to `<false/>` in the template's `godot_apple_embedded-Info.plist`. Do **not** add it again in `application/additional_plist_content` (duplicate key). |
| Orientation | Derived from project setting `display/window/handheld/orientation=1` (portrait) → `UISupportedInterfaceOrientations = [UIInterfaceOrientationPortrait]`. Not an export option. |
| Status bar / full screen | Template sets `UIStatusBarHidden=true`, `UIRequiresFullScreen=true`, `CADisableMinimumFrameDurationOnPhone=true` (allows 120 Hz on ProMotion iPhones). |
| Privacy manifest | `PrivacyInfo.xcprivacy` generated from `privacy/*` options. Engine-required-reason APIs kept at Godot defaults (file timestamp DDA9.1+C617.1, system boot time 35F9.1, disk space E174.1+85F4.1). `NSPrivacyTracking=false`, no collected data types. |
| Team ID | Export **refuses** to run while `application/app_store_team_id` is empty (`App Store Team ID not specified.`). The repo keeps it empty on purpose. |
| Signing | Generated project uses `CODE_SIGN_STYLE = Automatic`, identities "Apple Development" (Debug) / "Apple Distribution" (Release). |

### Preset values (`export_presets.cfg`)

| Option | Value | Note |
|---|---|---|
| `application/bundle_identifier` | `com.example.fruitfusion` | **PLACEHOLDER — MUST CHANGE** to your registered App ID |
| `application/app_store_team_id` | `""` | set locally only; never commit |
| `application/short_version` / `application/version` | `1.0.0` / `1` | CFBundleShortVersionString / CFBundleVersion. Bump `version` for every upload. |
| `application/targeted_device_family` | `0` (iPhone) | `TARGETED_DEVICE_FAMILY = "1"` in the project |
| `application/min_ios_version` | `15.0` | Godot 4.7.1 minimum (cannot go lower) |
| `application/export_method_release` | `0` (App Store) | `export_method_debug` = `1` (Development) |
| `application/export_project_only` | `true` | Only generate the Xcode project; archive in Xcode |
| `icons/icon_1024x1024` | `res://assets/icon/icon_1024.png` | Godot generates the full AppIcon set from it. Must be 1024×1024, **no alpha** |
| `storyboard/use_custom_bg_color` / `custom_bg_color` | `true` / #FDF2DE | Launch storyboard background |
| `storyboard/image_scale_mode` | `1` (Center) | Image = project `application/boot_splash/image` = `res://assets/icon/launch_logo.png` |
| entitlements (`game_center`, `push_notifications`, `increased_memory_limit`, `additional`) | off / Disabled / empty | No capabilities |
| `capabilities/*` | all off | (A12 requirement still added automatically, see above) |
| `privacy/*_usage_description` | empty | App uses no camera, microphone or photos. Note: the template still writes these three keys with empty strings into Info.plist. |
| `privacy/tracking_enabled` | `false` | No ATT prompt, no tracking domains |
| `user_data/accessible_from_files_app`, `..._itunes_sharing` | `false` | Save data stays private |
| `export_filter` | `all_resources`, exclude `tests/*, tools/*, store/*, docs/*, *.md` | |

### Export compliance (encryption)
The app uses no cryptography of its own (no network, no HTTPS, no encrypted PCK: `encrypt_pck=false`).
`ITSAppUsesNonExemptEncryption=false` is already in Info.plist via the template, so App Store Connect
should not ask the export-compliance question per build. If the app ever adds networking/encryption,
revisit this ([HUMAN-DECISION]).

---

## 2. Prerequisites (human)

- A Mac running a macOS version supported by the current Xcode.
- **Xcode 26 or later with the iOS 26 SDK.** Verified 2026-11-16 at
  <https://developer.apple.com/news/upcoming-requirements/>: *"Apps uploaded to App Store Connect must be
  built with Xcode 26 or later using an SDK for iOS 26 …"* (since April 28, 2026). Re-check this page
  before every release; Apple raises the minimum every spring.
- An **Apple Developer Program** membership (paid) — needed for App IDs, distribution signing,
  TestFlight and App Store.
- At least one physical iPhone (A12 or newer, iOS 15+) for device testing.
- Godot 4.7.1 stable for macOS + export templates 4.7.1 (same version string exactly).

## 3. Install Godot 4.7.1 and templates

1. Download Godot 4.7.1-stable (macOS universal) from the official site or
   <https://github.com/godotengine/godot/releases/tag/4.7.1-stable>.
2. Install templates: Editor → *Manage Export Templates* → *Download and Install*, or
   *Install from File* with `Godot_v4.7.1-stable_export_templates.tpz`.
   Only `ios.zip` and `version.txt` are needed for iOS. Manual install locations:
   - macOS: `~/Library/Application Support/Godot/export_templates/4.7.1.stable/`
   - Linux: `~/.local/share/godot/export_templates/4.7.1.stable/`
   `version.txt` must contain `4.7.1.stable`.
3. Open the project once in the editor (or run `godot --headless --path . --import`) so assets and
   translations are imported.

## 4. Export the Xcode project

### 4a. Set your local values (do not commit)
In Project → Export → iOS:
- `Application → App Store Team ID`: your 10-character Team ID (developer.apple.com → Membership).
- `Application → Bundle Identifier`: your real ID (e.g. `com.<yourcompany>.fruitfusion`).
Revert/stash these before committing, or keep them only in a local copy.

### 4b. From the Godot editor
Project → Export → iOS → *Export Project…* → choose an **empty folder outside the repo**, file name
`FruitFusion.xcodeproj`, untick *Export With Debug* for release.

### 4c. From the command line (works on Linux and macOS)
```sh
mkdir -p ~/build/ios
godot --headless --path /path/to/fruit-fusion --export-release "iOS" ~/build/ios/FruitFusion.xcodeproj
```
Verified on Linux (Godot 4.7.1 in the cloud container, 2026-11-16):
- With the repo preset as committed (empty Team ID) export is refused:
  ```
  ERROR: Cannot export project with preset "iOS" due to configuration errors:
  App Store Team ID not specified.
  ERROR: Project export for preset "iOS" failed.
  ```
- On a scratch copy with a dummy Team ID (`ABCDE12345`) and stub scripts/placeholder icon (the game code
  did not exist yet), export **completed** (exit code 0) and produced `FruitFusion.xcodeproj`,
  `FruitFusion/` (Info.plist, entitlements, `Launch Screen.storyboard`, `Images.xcassets` with all
  AppIcon sizes), `FruitFusion.pck`, `FruitFusion.xcframework`, `MoltenVK.xcframework`,
  `PrivacyInfo.xcprivacy`. Last lines:
  ```
  WARNING: Xcode Build: .ipa can only be built on macOS. Leaving Xcode project without building the package.
  WARNING: Project export for preset "iOS" completed with warnings.
  ```
  The generated `project.pbxproj` contained `IPHONEOS_DEPLOYMENT_TARGET = 15.0`,
  `PRODUCT_BUNDLE_IDENTIFIER = com.example.fruitfusion`, `MARKETING_VERSION = 1.0.0`,
  `CURRENT_PROJECT_VERSION = 1`, `TARGETED_DEVICE_FAMILY = "1"`, `CODE_SIGN_STYLE = "Automatic"`;
  the storyboard background was `red="0.992…" green="0.949…" blue="0.870…"` (#FDF2DE); the entitlements
  file was empty.
- So on Linux you can generate the Xcode project, but nothing can be compiled, signed or archived there.
  Copy the whole output folder to a Mac. A Dummy Team ID must be replaced in Xcode (Signing & Capabilities) if used.

Re-run the real export once the game code is complete; the orchestrator will record the result.

## 5. Register the App ID (Apple Developer account)

1. developer.apple.com → Certificates, IDs & Profiles → Identifiers → **+** → App IDs → App.
2. Explicit Bundle ID = the one you set in the preset. Capabilities: leave all **unchecked**
   (no Push, no Game Center, no In-App Purchase, no iCloud).
3. App Store Connect → My Apps → **+** New App: platform iOS, name (check availability of
   "Fruit Fusion"; fallbacks in `store/`), primary language, the bundle ID, a SKU.

## 6. Open in Xcode, sign, run on device

1. Open `FruitFusion.xcodeproj` in Xcode 26+.
2. Target *FruitFusion* → *Signing & Capabilities*: tick **Automatically manage signing**, choose your
   Team. Xcode creates the development certificate/profile. Confirm no capabilities are listed.
3. *General*: check Display Name "Fruit Fusion", Bundle Identifier, Version 1.0.0, Build 1,
   Minimum Deployments iOS 15.0, iPhone only, Portrait only.
4. Connect the iPhone, enable Developer Mode on it (Settings → Privacy & Security), select it as run
   destination, **Product → Run**. Execute `docs/ios/DEVICE_TEST_PLAN.md`.

## 7. Archive and upload

1. Destination: *Any iOS Device (arm64)*. Scheme config Release (Product → Scheme → Edit Scheme →
   Archive → Release).
2. **Product → Archive**.
3. Organizer → select archive → **Validate App** (fix any issue), then **Distribute App** →
   *App Store Connect* → *Upload* (automatic signing; Xcode creates the distribution certificate/profile).
4. Every new upload needs a higher Build number (`application/version` in the preset, or in Xcode).

## 8. TestFlight

Follow `docs/ios/TESTFLIGHT_CHECKLIST.md`. Internal testers get builds after processing; external
testers require Beta App Review.

## 9. App Store submission

1. App Store Connect → the app → version 1.0.0: fill metadata from `store/`, screenshots from
   `store/screenshots/`, privacy policy URL and App Privacy answers from `docs/privacy/`
   ("Data Not Collected"), age rating questionnaire, category (Games → Puzzle), pricing.
2. Select the processed build, answer export compliance if asked (no encryption).
3. Submit for Review. Choose manual or automatic release.

See `RELEASE_CHECKLIST.md` for the full tagged list.

## 10. Troubleshooting notes

- *"App Store Team ID not specified"* → set the Team ID locally (§4a).
- *Export template not found* → template version folder must be exactly `4.7.1.stable`.
- *Icon has alpha* → App Store rejects icons with transparency; `assets/icon/icon_1024.png` must be RGB.
- *Missing launch logo* → Godot falls back to its default splash image; check `assets/icon/launch_logo.png`
  exists before exporting (Center mode shows it at pixel size ÷ screen scale).
- Godot comments in `export_presets.cfg` are dropped when the editor re-saves the file — the
  must-change notes are duplicated here.
