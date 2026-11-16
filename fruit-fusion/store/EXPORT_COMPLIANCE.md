# Export compliance (encryption) — v1.0

**Answer: the app does not use non-exempt encryption.** `ITSAppUsesNonExemptEncryption = NO`.

Reasoning:
- The game makes no network connections and implements no cryptography of its own.
- Save files are plain JSON in the app sandbox; the PCK is not encrypted (`encrypt_pck=false` in `export_presets.cfg`).
- Only encryption built into iOS itself is used implicitly (Data Protection), which is exempt.
- Even future HTTPS-only use (e.g. an ad SDK over the OS's TLS) is normally still exempt; re-check then.

Where it is set:
- The Godot 4.7.1 iOS template Info.plist (`templates/ios.zip` → `godot_apple_embedded/godot_apple_embedded-Info.plist`)
  already contains `<key>ITSAppUsesNonExemptEncryption</key><false />` — verified by inspection. Developer must confirm
  it is still present in the exported project's Info.plist.
- With the key present, App Store Connect will not ask the encryption question for each build. If it does ask:
  "Does your app use encryption?" → **No** (or: "None of the algorithms mentioned above" / exempt only).

No CCATS, no year-end self-classification report, no French encryption declaration is needed for this answer.

This is a legal declaration made by the developer under US export rules (EAR); the developer confirms it.
