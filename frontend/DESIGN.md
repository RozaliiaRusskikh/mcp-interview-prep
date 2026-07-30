# Design concept: Recruiter's desk

A card-catalog / personnel-dossier read, not a messaging-app chat. This is literally
true to the architecture: the backend tags every answer `deterministic` (filed fact
from resume/situations JSON) or `llm` (improvised). Most chat UIs have nothing real to
say about provenance — this one does, so the design shows it.

Tokens live in [src/index.css](src/index.css) (`@theme` block) — this doc is the
rationale behind them, not a second copy of the values.

## Color
- `paper` `#F5F1E6` — page background, bone paper (brightened from an earlier, dimmer draft)
- `card` `#FFFDF8` — elevated card surface (brightened to near-white)
- `ink` `#1E2A3A` — text/display, deep navy-charcoal
- `stamp` `#A7362A` — filed/deterministic tag, rubber-stamp oxblood (not terracotta)
- `ledger` `#1E7A46` — llm/improvised tag, all action buttons (chips + submit), focus
  states. Shifted from a muted teal to a true emerald at Roza's request — "ledger
  green" still fits: bookkeepers historically wrote ledgers in green ink, so the name
  didn't need to change, just the value.

## Type
- **Fraunces** (display) — restrained, headline only
- **Inter** (body) — conversation text
- **IBM Plex Mono** (utility) — uppercase tracked-out labels, source stamps,
  sequential numbering — ties to the JSON-data spine of the app

## Layout
Single column, max-width ~700px. Each answer is a squared-corner card (zero-radius is
literal here — real index cards have sharp corners, not a trend) with a rotated corner
stamp reading its actual source: "FILED — Situations/Conflict" in oxblood, or
"IN ROZA'S WORDS" in ledger green for the Gemini fallback. Questions render as
centered slips in a plain white card (`bg-card`, neutral `border-ink/15`) — no color
coding, since a question has no "source" to tag; ledger green is reserved for the
answer side. Sequential numbering ("Question 001", 002…) is honest here — it's a real
transcript, not decorative.

Each assistant-side card (answer, loading, error) carries a small square avatar —
`AssistantIcon` in `src/Chat.tsx` — representing "the assistant" persona the copy now
refers to. The header photo uses the same file (`public/roza-bot-avatar.png`) for
now — swap it for an actual headshot in `public/` and update the `src` in
`Chat.tsx` whenever one's available.

A "Recommendations" section (`src/recommendations.ts`) sits below the transcript,
always visible regardless of conversation state — real LinkedIn recommendations,
each in its own card with a "Recommendation" corner tag (neutral ink, not
oxblood/green, since a third-party endorsement is neither a filed fact nor an LLM
answer — it's its own category of provenance). Each card also states the specific
relationship (managed directly / mentor / teacher / colleague at a different company)
rather than summarizing all five under one label like "colleagues," which wasn't
accurate for a manager or a teacher. Duplicated from `../data/recommendations.json`
for now since there's no backend/API yet for the frontend to fetch it from; keep both
in sync until Phase 2 exists.

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
The corner stamp. One risk, spent in one place; everything else stays quiet.

## Self-check against generic AI-frontend defaults
- Not cream+terracotta-serif: oxblood/ledger-teal read archival, not warm-minimal.
- Not dark+neon-accent.
- Not zero-radius broadsheet columns: single-column chat, hairline rules only where a
  real index card would have them.
