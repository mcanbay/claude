# App name options

## Status of "Fruit Fusion"

App Store app names must be unique across the store (per localized name). A web search on 2026-11-16 found
several existing listings that start with or contain "Fruit Fusion", including fruit-merging games:

- "Fruit Fusion - Watermelon Game" (https://apps.apple.com/us/app/id6470950830) — a fruit-merging game, i.e. the same genre
- "Fruit Fusion Fun" (https://apps.apple.com/us/app/id6473606866) — also a fruit-merging game
- "Fruit Fusion Master" (https://apps.apple.com/us/app/-/id6754099573), "Fruit Fusion Crush - Match 3" (https://apps.apple.com/us/app/id1149251979), "Fruit Match Fusion" (https://apps.apple.com/us/app/id6754098010)

Conclusions:
- The bare name **"Fruit Fusion" is probably not available** or only just; even if it is, the brand would be easily
  confused with an existing game in the same genre. That is a risk under Guideline 4.1 (copycats / confusingly
  similar names) and 5.2 (IP), and a trademark risk.
- The metadata in `store/metadata/` currently uses **"Fruit Fusion: Jar Puzzle"** (EN, 24 chars) and
  **"Fruit Fusion: Meyve Kavanozu"** (TR, 28 chars) as working names. These are more distinctive, but they still
  start with the crowded "Fruit Fusion" phrase. **Recommendation: pick a name from the list below** (or another original
  name) unless the human is happy with the risk.
- Web search is not the App Store Connect name check. Nothing below has been verified as available.

## Fallback names (original, ≤ 30 characters)

| # | English (chars) | Turkish (chars) | Idea |
|---|---|---|---|
| 1 | Jarful: Fruit Merge (19) | Jarful: Meyve Birleştir (23) | invented word, jar + "jarful" |
| 2 | Orchard Drop (12) | Bahçe Düşür (11) | orchard theme, the drop mechanic |
| 3 | Pome & Quince (13) | Nar ile Ayva (12) | the game's Anatolian fruits |
| 4 | Fruit Jar Fuse (14) | Meyve Kavanozu (14) | plain, descriptive |
| 5 | Juicy Jar Merge (15) | Sulu Kavanoz (12) | playful |
| 6 | Pantry Pop: Fruit Merge (23) | Kiler Pop: Meyve Birleştir (26) | "kiler" = pantry |
| 7 | Bostan Merge (12) | Bostan Birleştir (16) | "bostan" = Turkish kitchen garden |
| 8 | Ripen Up: Merge Puzzle (22) | Olgunlaştır: Meyve Bulmacası (28) | growth/ripening |
| 9 | Fusion Jar (10) | Füzyon Kavanoz (14) | keeps the "fusion" idea, drops "fruit" |
| 10 | Grow the Fruit (14) | Meyveyi Büyüt (13) | verb-style, matches subtitle |

Notes:
- Avoid names that contain other games' names, "watermelon game", "suika", "2048" etc. — keywords/titles that ride
  on another product are rejected under 2.3.7 / 4.1 and can trigger IP complaints.
- The Turkish and English names may differ; each localized name must itself be unique.
- If the final name changes, also update `config/name` / `config/name_localized` in `project.godot` (owned by
  game-architect) so the Home-screen name (CFBundleDisplayName) matches, and update `name.txt` files and the
  privacy-policy app name.

## What the human must do

1. In App Store Connect → Apps → "+" → New App, type the chosen name. App Store Connect tells you immediately if the
   name is already in use (the name can be reserved this way; unused reservations can be lost after a while).
2. Do a trademark search at least in the target markets: TÜRKPATENT (Türkiye), EUIPO TMview (EU), USPTO (US),
   WIPO Global Brand Database. Class 9 (software/games) and 41 (entertainment) are the relevant classes.
3. Optionally check the domain / social handles you want for the support and marketing URLs.
4. A trademark opinion is a legal question — this file is not legal advice.
