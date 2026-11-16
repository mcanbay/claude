# Human-only actions and decisions

Nothing in this list can be done by the agents (no Apple account, no Xcode, no legal authority). Order is roughly the
order to do them in.

## Accounts and identity
1. **Enrol in the Apple Developer Program** (99 USD/year, individual or organisation). An organisation needs a D-U-N-S
   number and takes longer. Decide which — it determines the **seller name** shown on the App Store
   (individual = your legal personal name; organisation = the legal entity name).
2. Accept the latest Program License Agreement and, in App Store Connect → Business, the **Free Apps agreement**
   (accepted automatically with the membership). The **Paid Apps agreement, tax forms and banking are not needed for a
   free app without IAP**; they become necessary before adding paid features. (Ad revenue goes through the ad network,
   not Apple, but the ad network will want its own tax/payment details.)
3. **EU Digital Services Act trader status** (App Store Connect → Business / App information): required to distribute in
   EU storefronts. Declare whether you are a "trader" (acting for business/commercial purposes — usually yes if you
   monetise or run it as a business). Traders must provide address, phone and email, which are then **shown publicly
   on the EU App Store page**. If you do not want to declare, remove the EU storefronts from availability.

## App setup in App Store Connect
4. **Bundle ID**: register an explicit App ID at developer.apple.com (e.g. `com.<yourdomain>.<appname>`) and give it to
   ios-release-engineer to replace `com.example.fruitfusion` in `export_presets.cfg`. It cannot be changed after the
   first upload.
5. **App name**: choose the final name, check availability in App Store Connect (create the app record), and run a
   trademark search — see `NAME_OPTIONS.md`. Set **SKU** (any internal string, e.g. `fruitjar-ios-001`).
6. **Primary language**: Turkish (choose per your main market); add English (U.S.) localization. Consider adding
   English (U.K.) or leaving U.S. only.
7. **Category**: Primary *Games*, subcategories *Puzzle* and optionally *Casual*. Secondary category optional
   (e.g. *Entertainment*).
8. **Pricing and availability**: price tier (Free assumed), territories (all, or a selection; see DSA above),
   pre-order (no), availability on Apple-silicon Macs and Apple Vision Pro for an iPhone-only app (decide; untick if
   you have not tested).
9. **Content Rights**: answer "Does your app contain, show or access third-party content?" → No (all original, OFL
   font). Confirm the font licence actually used.
10. **Age rating** questionnaire (`AGE_RATING.md`), **App Privacy** (`APP_PRIVACY.md`), **export compliance**
   (`EXPORT_COMPLIANCE.md`), **App Review contact + notes** (`REVIEW_NOTES.md`).
11. **Copyright line** (e.g. `© 2026 <<seller name>>`).
12. **Routing app coverage / Game Center / iCloud**: none.

## Web presence
13. **Host the privacy policy** (`docs/privacy/PRIVACY_POLICY_tr.md` and `_en.md`) at a public HTTPS URL, after
   filling placeholders and reviewing them — the legal declaration is yours. GitHub Pages or any static host is fine.
14. **Support URL**: a page that actually contains a way to contact you (email/form). Required by Apple. Marketing URL
   is optional (delete `marketing_url.txt` if not used).
15. Replace the `REPLACE-ME.example` URLs in `store/metadata/*/{support,marketing,privacy}_url.txt`.
16. Provide a **support email** that you monitor.

## Build, test, submit
17. Export with Godot on a Mac, open in Xcode, set the team, archive, verify the **privacy manifest** and the
   **Generate Privacy Report** output, check `ITSAppUsesNonExemptEncryption` (see `APP_PRIVACY.md`,
   `EXPORT_COMPLIANCE.md`, `docs/ios/`).
18. TestFlight on at least one physical iPhone; play through both languages; check iPad compatibility mode.
19. Upload screenshots (`SCREENSHOT_PLAN.md`) after checking they show the real final build.
20. Review all metadata texts once more for claims that the final build does not support.
21. Submit for review; choose manual or automatic release; optionally phased release (not relevant for v1).

## Later (when adding ads)
22. Choose ad network, accept its terms, set up its account and payout/tax, implement consent (GDPR/KVKK) and ATT,
   then redo App Privacy, privacy policy, age rating (Advertising = Yes) and metadata ("no ads" claims) — see
   `APP_PRIVACY.md`.

## Legal reminders
- Privacy policy, App Privacy answers, export compliance, content rights and DSA trader status are **legal declarations
  by the account holder**. The drafts here are not legal advice.
- If you operate as a business in Türkiye, check whether VERBİS registration applies (generally not required when no
  personal data is processed, and there are exemptions for small controllers) — confirm with a professional.
