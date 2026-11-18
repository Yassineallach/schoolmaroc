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

- `NearshelfTopBar`: every screen's app bar, on the page colour. `large` for top-level tabs (serif 24), back arrow and serif 20 for detail screens.
- `PaperSearchField` + `FieldHint`: the white search field (hairline edge, brown edge on focus) and its "Tip" footnote. Home, Add library, branch picker.
- `LibraryRow`: monogram, name, location, service tags (filled = digital, outlined = physical catalog), with `trailing` and `footer` slots. Home, Libraries, Add library. `LibraryRowSkeleton` while loading.
- `SectionHeader`: serif title, optional count, one text action aligned to the gutter.
- `ListRow`, `RowDivider` (inset to the text column), `Monogram`, `CoverThumb` (cloth-binding placeholder), `Tag`.
- `EmptyState`: icon tile, serif title, one line of help, at most one action.
- `NearshelfNavBar`: 64 dp, page-coloured, hairline above, short accent rule over the selected tab.
- Buttons (`Buttons.kt`): filled primary (one per screen); `accentTonalColors` for borrow/watching; outlined with `hairline()` + `quietOutlinedColors` for secondary; all `ButtonShape`.
- Status: `Badge` Success/Warning are tinted labels (`StatusColors.*Container`), never saturated fills.
- Native ad card (`res/layout/native_ad_card.xml`): compact, about 144 dp: 120 dp media square on the left (AdMob minimum for video), "Ad" label, icon, headline and action on the right; no body text (optional under AdMob policy). White card, hairline, Instrument Sans.

Home has three layers: a warm top panel (surfaceContainer, 28 dp bottom corners, under the status bar) with the raised white search field; the libraries in one white card; recent covers with a soft shadow standing on a thin shelf line.

Results are organised by format, not by library (`ResultsOrganizer.kt`): three fixed tabs (eBook | Audiobook | Print), pinned under the book, each with its status under the label ("Now", "28 days", "Hoopla", "On shelf", "None"). The page opens on the preferred format if a library has it, otherwise the one available soonest. A tab shows a one-line verdict when there is a choice to sum up, then every option from every library ranked fastest first (available now, then hoopla, then shortest wait). Every option, in every tab, is the same card (`OptionCard`): library tile and name, status label (Available / Waitlist / Instant or Flex / On shelf / All copies out), tags for what tells options apart (the service for eBook and Audiobook, an edition or language), the figures Total copies | Holds | Days wait or Available, then for print the home or nearest branch with "Show all N branches" inside the card, and one full-width action. Distances over 200 km are not shown. Other-language editions collapse under one line. Everything that isn't a result (not found, still checking, failures) goes to an "Also checked" footer. Catalog software names (BiblioCommons, Polaris…) are never shown as such: it's "the library catalog".

## Rules

- Light and dark both use the tokens; check new screens in both (`./gradlew :app:testDebugUnitTest -Pnearshelf.screenshots=true`).
- Respect "Remove animations" (`rememberReducedMotion`); animations 150–200 ms, only for state changes.
- Prefer wrapping to truncation; when truncating, keep the full text in semantics.
- Large font sizes: stack side-by-side actions (fontScale ≥ 1.5); bars grow instead of clipping.
