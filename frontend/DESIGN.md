# Design concept: Recruiter's desk

A card-catalog / personnel-dossier read. Originally conceived as deliberately *not* a
messaging-app chat (everything centered, like filed index cards, no left/right
bubbles) — since revised: questions are right-aligned, assistant answers left-aligned,
adopting the familiar messaging-app convention (iMessage/WhatsApp/Slack/ChatGPT all use
it) for instant "who said what" scannability.

Tokens live in [src/index.css](src/index.css) (`@theme` block) — this doc is the
rationale behind them, not a second copy of the values.

## Color
- `paper` `#F5F1E6` — bone paper (brightened from an earlier, dimmer draft)
- `card` `#FFFDF8` — elevated card surface (brightened to near-white)
- `ink` `#1E2A3A` — text/display, deep navy-charcoal
- `stamp` `#A7362A` — filed/deterministic tag, rubber-stamp oxblood (not terracotta)
- `ledger` `#1E7A46` — llm/improvised tag, all action buttons (chips + submit), focus
  states. Shifted from a muted teal to a true emerald at Roza's request — "ledger
  green" still fits: bookkeepers historically wrote ledgers in green ink, so the name
  didn't need to change, just the value.
- `green` `#F0F4E8` — page background wash (`body`).

## Type
- **Fraunces** (display) — restrained, headline only
- **Inter** (body) — conversation text
- **IBM Plex Mono** (utility) — uppercase tracked-out labels, source stamps,
  sequential numbering — ties to the JSON-data spine of the app

## Layout

Each assistant-side card (answer, loading, error) carries a small square avatar —
`AssistantIcon` in `src/components/AssistantIcon.tsx` — representing "the assistant"
persona the copy refers to, using `public/roza-bot-avatar.png` (an illustrated
avatar, distinct from the real headshot `public/roza.jpg` used in the page header).

A "Recommendations" page (`src/pages/RecommendationsPage.tsx`, its own route rather
than a section on the chat page) lists real LinkedIn recommendations, each in its own
card (`src/components/RecommendationCard.tsx`) — no corner tag (removed along with the
chat answer tags, for the same reason: uniform cards over per-item source labeling).
Each card states the specific relationship (managed directly / mentor / teacher /
colleague at a different company) rather than summarizing all under one label like
"colleagues," which wasn't accurate for a manager or a teacher. Data lives in
`src/constants/recommendations.ts`, duplicated from `../data/recommendations.json`
since there's no backend/API yet for the frontend to fetch it from; keep both in sync
until Phase 2 exists.

Quotes are clamped to 11 lines (`line-clamp-11` on the quote paragraph) — chosen
because that's Michael Farquhar's natural, untruncated line count, i.e. the shortest
"full" card sets the baseline rather than an arbitrary number. `RecommendationCard`
detects real overflow via `scrollHeight > clientHeight` (not a character-count guess,
which breaks under wrapping) and only then shows "Read more". That opens
`RecommendationModal` — a small overlay, not an inline expand — specifically so
expanding a long quote never reflows the grid or shifts anything else on the page.

## Interaction
Hover feedback is color/shade only, everywhere — no translate/lift/shadow motion was
kept on any button once tried, by direct instruction. Every clickable element
(chips, Ask button, links, Read more, modal close) sets `cursor-pointer` explicitly
rather than relying on browser defaults.

## Signature
The cursive header tagline (`font-script`, Caveat) — one handwritten-feeling flourish
against an otherwise typographically restrained, monospace-and-serif system.

## Self-check against generic AI-frontend defaults
- Not cream+terracotta-serif: oxblood/ledger-teal read archival, not warm-minimal.
- Not dark+neon-accent.
- Not zero-radius broadsheet columns: single-column chat, hairline rules only where a
  real index card would have them.
