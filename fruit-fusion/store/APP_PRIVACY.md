# App Privacy ("nutrition label") answers — v1.0

Applies to: v1.0 as described in `CLAUDE.md` / `GAME_DESIGN.md` (offline, no ads, no IAP, no analytics, no SDKs).
Re-check before every release; the answers are a legal declaration by the developer (Account Holder).

## App Store Connect → App Privacy

| Question | Answer |
|---|---|
| Privacy Policy URL | the hosted URL of `docs/privacy/PRIVACY_POLICY_en.md` (see `privacy_url.txt`, still a placeholder) |
| User Privacy Choices URL (optional) | leave empty |
| "Do you or your third-party partners collect data from this app?" | **No, we do not collect data from this app** |
| Resulting label | **Data Not Collected** |
| Tracking (App Tracking Transparency) | **No tracking.** No IDFA, no `AppTrackingTransparency` prompt, no `NSUserTrackingUsageDescription` |

Why "not collected" is correct: Apple defines *collect* as transmitting data off the device in a way that the
developer or partners can access it for longer than needed to service the request in real time. v1 stores best score,
settings and the current run only as JSON files in the app sandbox (`user://`), never sends anything anywhere, and has
no crash reporter, analytics or ad SDK. Data that stays on the device is not "collected".

Note: if the user has iCloud Backup enabled, iOS may back up the app sandbox. That is an OS-level backup
controlled by the user and Apple, not collection by the developer. Same for Apple's own opt-in crash/analytics data
shared with developers ("App Analytics", "Crashes" in App Store Connect) — Apple says this does not need to be declared.

## Repo verification (done by app-store-compliance)

- `grep` over `*.gd`, `*.tscn`, `*.godot`, `*.cfg` for `HTTPRequest`, `HTTPClient`, `StreamPeerTCP/TLS`, `PacketPeerUDP`,
  `WebSocket`, `ENet`, `MultiplayerPeer`, `OS.shell_open`, `OS.get_unique_id`, `JavaScriptBridge`,
  `Engine.get_singleton` (plugins), `AdMob`, `Firebase`, `Analytics` → **no matches** at the time of writing.
  **Caveat:** `src/` was still empty when this was checked (code is written concurrently). Re-run the grep below on the
  final code before submission.
- `export_presets.cfg`: `privacy/tracking_enabled=false`, `privacy/tracking_domains` empty, `capabilities/access_wifi=false`,
  `modules/camera=false`, no camera/microphone/photo usage descriptions, Game Center and push disabled.

```sh
cd fruit-fusion
grep -rnE 'HTTPRequest|HTTPClient|StreamPeerTCP|StreamPeerTLS|PacketPeerUDP|WebSocket|ENet|MultiplayerPeer|OS\.shell_open|get_unique_id|JavaScriptBridge|Engine\.get_singleton|AdMob|Firebase|Analytics' \
  --include=*.gd --include=*.tscn --include=*.godot --include=*.cfg .
# expected: no output (a shell_open to open the privacy policy in Safari would be fine, but must be reviewed)
```

## Privacy manifest (`PrivacyInfo.xcprivacy`) — Godot 4.7.1

Inspected read-only: `/opt/godot/templates.tpz` → `templates/ios.zip` (version.txt = `4.7.1.stable`).

- The iOS template **ships `PrivacyInfo.xcprivacy`** at the project root and it is already in the Xcode project's
  Resources build phase (`project.pbxproj` references `PrivacyInfo.xcprivacy in Resources`).
- In the template it is a stub with placeholders `$priv_api_types`, `$priv_tracking`, `$priv_collection`; the Godot
  exporter fills these from the `privacy/*` export options:
  - `privacy/file_timestamp_access_reasons` → `NSPrivacyAccessedAPICategoryFileTimestamp`
  - `privacy/system_boot_time_access_reasons` → `NSPrivacyAccessedAPICategorySystemBootTime`
  - `privacy/disk_space_access_reasons` → `NSPrivacyAccessedAPICategoryDiskSpace`
  - `privacy/active_keyboard_access_reasons` → `NSPrivacyAccessedAPICategoryActiveKeyboards`
  - `privacy/user_defaults_access_reasons` → `NSPrivacyAccessedAPICategoryUserDefaults`
  - `privacy/tracking_enabled` / `privacy/tracking_domains` → `NSPrivacyTracking` / `NSPrivacyTrackingDomains`
  - `privacy/collected_data/<type>/{collected,linked_to_user,used_for_tracking,collection_purposes}` → `NSPrivacyCollectedDataTypes`
- Current preset values: file timestamp `3`, system boot time `1`, disk space `3`, active keyboard `0`, user defaults `0`
  (these are bit flags selecting Apple reason codes; they are the ios-release-engineer's defaults for the engine's own
  API usage). The template Info.plist also already contains `ITSAppUsesNonExemptEncryption = false`.

What the developer must verify in the **exported Xcode project** (cannot be done on Linux):
1. Open `PrivacyInfo.xcprivacy` in Xcode: it is valid XML (no leftover `$priv_...` text), `NSPrivacyTracking = NO`,
   `NSPrivacyTrackingDomains` empty/absent, `NSPrivacyCollectedDataTypes` empty.
2. `NSPrivacyAccessedAPITypes` lists FileTimestamp, SystemBootTime and DiskSpace with reason codes that are true for
   the app (engine use: e.g. `C617.1` file timestamps inside the app container, `35F9.1` elapsed time, `E174.1`/`85F4.1`
   disk space). If Xcode or App Store Connect reports a missing required-reason API (e.g. UserDefaults `CA92.1`),
   enable the matching option in the export preset — ask ios-release-engineer — rather than editing by hand each export.
3. Product → Archive → Generate Privacy Report (Organizer): the report must show no collected data and no tracking.
4. After upload, read the App Store Connect / email feedback for ITMS-91053 ("Missing API declaration") and fix any
   item it lists.
5. Info.plist has no `NSUserTrackingUsageDescription` and no camera/microphone/photo/location usage strings.

## If rewarded ads (or anything networked) are added later

The answers above become **wrong** the moment an ad SDK is linked, even if ads are not shown yet. Before such a release:

1. Re-answer App Privacy: typically at least *Identifiers → Device ID* (IDFA/IDFV), *Usage Data → Advertising Data /
   Product Interaction*, *Diagnostics → Crash/Performance Data*, often *Location → Coarse Location* (from IP), with
   purposes *Third-Party Advertising* and/or *Analytics*; mark "used for tracking" where the SDK tracks. Use the ad
   network's own App Store privacy disclosure document — answer for the SDK's real behaviour.
2. If any data is used for tracking (personalised ads, sharing IDFA): add ATT prompt (`AppTrackingTransparency`) with a
   `NSUserTrackingUsageDescription` in TR and EN, request permission **before** any tracking, set
   `privacy/tracking_enabled=true` and the SDK's tracking domains. Otherwise use non-personalised ads only.
3. The ad SDK must ship its own signed privacy manifest (it is on Apple's list of commonly used SDKs needing a
   manifest + signature for most ad networks). Verify in the Xcode privacy report.
4. EU/UK/TR consent: a consent management platform (e.g. Google UMP / IAB TCF) for GDPR, and KVKK explicit-consent /
   transfer-abroad wording; update both privacy policies (sections on ads, third parties, international transfers).
5. Age rating: answer "Advertising" = Yes in the age-rating questionnaire; if the app might be considered for kids,
   ad SDKs must comply with Guideline 1.3/5.1.4 (no behavioural ads to children).
6. Update the metadata: remove "No ads" from `description.txt` (EN + TR) and the screenshot captions if any.
7. App Store "Network" behaviour changes: `capabilities/access_wifi` is not needed for internet, but ATS settings must
   be checked (HTTPS only).
