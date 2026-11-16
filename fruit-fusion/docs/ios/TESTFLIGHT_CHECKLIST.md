# TestFlight checklist — Fruit Fusion

Nothing on this list has been executed yet. All steps need a Mac with Xcode 26+ and/or an Apple
Developer account. Tick items only after doing them yourself.

## Before archiving
- [ ] Real bundle identifier set (not `com.example.fruitfusion`), App ID registered with no capabilities.
- [ ] Team ID set locally, **not** committed.
- [ ] `application/short_version` = marketing version (e.g. `1.0.0`); `application/version` (build) higher than any build already uploaded for this version.
- [ ] Fresh export from Godot 4.7.1 into an empty folder (see BUILD_AND_RELEASE.md §4).
- [ ] App runs on at least one physical iPhone (DEVICE_TEST_PLAN.md smoke section passed).
- [ ] `assets/icon/icon_1024.png` is 1024×1024 RGB without alpha.

## Archive and upload
- [ ] Xcode: destination *Any iOS Device (arm64)*, Archive uses Release configuration.
- [ ] Product → Archive succeeded.
- [ ] Organizer → Validate App: no errors.
- [ ] Distribute App → App Store Connect → Upload succeeded.
- [ ] Email / App Store Connect shows the build as processed (can take 5–30+ min). Read any "ITMS-" warning email (e.g. privacy manifest, usage descriptions).

## App Store Connect → TestFlight
- [ ] Export compliance: should not be asked (Info.plist has `ITSAppUsesNonExemptEncryption=false`). If asked: "No" — the app uses no encryption.
- [ ] "What to Test" notes filled in (EN, optionally TR): core loop, save/resume, settings, language switch.
- [ ] Internal testing group created; testers added (App Store Connect users, up to 100).
- [ ] Internal testers install via the TestFlight app and confirm launch.
- [ ] (Optional) External group: Test Information (beta description, feedback email, privacy policy URL from `docs/privacy/`) filled; build submitted to Beta App Review; approved.
- [ ] Collect feedback/crashes in TestFlight → Feedback/Crashes; triage before App Store submission.
- [ ] TestFlight builds expire after 90 days — re-upload if needed.

## Exit criteria for App Store submission
- [ ] No crash reports for the candidate build on at least two different iPhone models.
- [ ] DEVICE_TEST_PLAN.md full matrix done on the candidate build.
- [ ] Same build number selected in the App Store version page.
