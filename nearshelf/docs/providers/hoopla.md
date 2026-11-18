# Hoopla: investigation (2026-11-18)

Findings from the public hoopladigital.com web app (Next.js + Apollo), verified with live requests.
No login was used.

## Endpoints

| Purpose | Request | Notes |
|---|---|---|
| Library lookup | `GET https://patron-api-gateway.hoopladigital.com/core/libraries/autocomplete?query={text}` with headers `app: WWW`, `ws-api: 2.1` | Up to 10 libraries: `id`, `name` ("Los Angeles Public Library (CA)"), `city`, `state`, `country`, `latitude`, `longitude`, `circsPerPatronMonth`. No credentials in this response. |
| Title search | `POST https://patron-api-gateway.hoopladigital.com/graphql`, same headers, `search(criteria: {q, pagination})` | Anonymous. Hits include `id`, `title`, `subtitle`, `isbn`, `language.name`, `kind.name` (EBOOK, AUDIOBOOK, COMIC, MOVIE, MUSIC, TELEVISION), `authors`. One request per search. |
| Deep link | `https://www.hoopladigital.com/title/{id}` | 200 with og:title. `assetlinks.json` delegates all hoopladigital.com URLs to `com.hoopladigital.android`. |

## What does not work anonymously

- **Per-library scope.** Search runs against Hoopla's whole catalog. Library scope (and `availability`
  filters, `licenseType`, `status`) comes from the signed-in patron; anonymously they are null or ignored.
- **Instant vs Flex.** `licenseType` is null without a login, so a title can't be labelled Instant
  (borrow now) or Flex (one copy, holds) up front.
- **Exact ISBN search.** `q` is free text; an ISBN matches digits inside unrelated titles.
- **Library feature flags.** `enablePpu`, `enableEst`, `enableHolds` read `false` for Los Angeles and
  Seattle, which offer Hoopla, so they don't mean what their names suggest. Not used.

## Do not use

`GET /core/libraries/{id}` (single library) returns fields named `patronAuthUserName` and
`patronAuthPassword` in its public response. Nearshelf never calls it, and no response from it is
stored as a fixture. Hoopla should be told (responsible disclosure).

## Examples

- "project hail mary": top hit is the **Italian** audiobook (ISBN 9788852153945). Penguin Random House
  doesn't license to Hoopla, so the English edition isn't there.
- "the martian andy weir": only study aids ("… | Conversation Starters", "… | Summary & Analysis").
