# Nearshelf design system

Source of truth in code: `app/src/main/kotlin/com/mardev/nearshelf/ui/theme/` (Theme.kt, Type.kt, Shape.kt).
Started from the [ui-ux-pro-max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) "book brown + page amber" system and refined to the brief below; checked against its Jetpack Compose stack rules and UX quick reference.

## Colour

| Role | Light | Dark | Use |
|---|---|---|---|
| background / surface | #FAF9F6 | #161412 | page |
| onSurface | #292722 | #EDE8E1 | primary text |
| onSurfaceVariant | #6F6B64 | #A9A39B | secondary text (≥4.5:1 on every surface) |
| primary | #75452D | #D9A784 | the one accent: wordmark, primary button, links, selection |
| secondary | #A77A57 | #C49A76 | icons and rules only (3.6:1, never small text) |
| surfaceContainer | #F1EEE8 | #211E1B | subtle surfaces: tags, tiles, secondary button |
| surfaceContainerLowest | #FFFFFF | (dark uses surfaceContainerHigh) | search field |
| outlineVariant | #E6E1D9 | #35312C | hairlines and borders |

Availability colours (available / waitlist) live in `LocalStatusColors`, outside the accent.

## Type

Two families, both OFL and bundled: **Newsreader** (serif) for the wordmark, headlines, section titles, book titles and headline numbers; **Instrument Sans** for everything read in passing or tapped.

| Token | Family | Size/line (sp) | Weight |
|---|---|---|---|
| Wordmark | Newsreader | 24/28 | 600 |
| headlineSmall | Newsreader | 24/30 | 500 |
| titleLarge (section titles, app bar) | Newsreader | 20/26 | 600 |
| BookTitleSmall | Newsreader | 15/19 | 600 |
| titleMedium (row titles) | Instrument Sans | 16/22 | 600 |
| bodyLarge / bodyMedium / bodySmall | Instrument Sans | 16/24 · 14/20 · 12/16 | 400 |
| labelLarge (buttons, actions) | Instrument Sans | 14/20 | 600 |
| TagLabel | Instrument Sans | 12/16 | 500 |

No text below 12 sp. Text styles come from tokens, never inline sizes.

## Space and shape

- 4 dp grid: `Space.xs 4 · s 8 · m 12 · l 16 · xl 24 · xxl 32`; screen gutter 20 dp.
- Corners: 4 covers and tags · 8 tiles · 10 controls (fields, buttons: `ControlShape`) · 12 cards. No pills.
- Touch targets ≥ 48 dp; rows ≥ 72 dp; buttons 48 dp; search field 52 dp.

## Components (`ui/components`)

- `SectionHeader`: serif title, optional count, one text action aligned to the gutter.
- `ListRow`, `RowDivider` (inset to the text column), `Monogram`, `CoverThumb`.
- `Tag`: filled = digital service, outlined = physical catalog.
- `NearshelfNavBar`: 64 dp, page-coloured, hairline above, short accent rule over the selected tab.
- Buttons: filled primary (one per screen), tonal secondary on `surfaceContainer`; both `ButtonShape`.

## Rules

- Light and dark both use the tokens; check new screens in both (`./gradlew :app:testDebugUnitTest -Pnearshelf.screenshots=true`).
- Respect "Remove animations" (`rememberReducedMotion`); animations 150–200 ms, only for state changes.
- Prefer wrapping to truncation; when truncating, keep the full text in semantics.
- Large font sizes: stack side-by-side actions (fontScale ≥ 1.5); bars grow instead of clipping.
