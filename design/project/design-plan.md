# Appeal Architect — Design Plan

> **Revised after the Pass 2 visual audit.** Dark mode removed; palette rebuilt around
> forest + clay on warm paper; the landing page re-set on a Swiss grid (rules and columns
> instead of cards, radius dropped to 0–2px on the marketing page). Sections 1 and 3 below
> are superseded by `tokens.css`, which is the source of truth.

**Subject:** the dossier. **Gesture:** the margin note. **Rule:** colour means time or standing, nothing else.

---

## 0. The one idea

A denial letter is a document that makes a claim. This product writes in the margin next to it.

So the whole system is **desk → paper → margin**. A warm grey ground is the desk. Light panels are paper laid on it. Quoted insurer language sits in a measured column with a hanging rule, and the counter-argument sits *beside* it, attached by a hairline with a square terminal. That one relationship — quoted claim left, refutation right, connected — is the argument graph, the extraction review, the letter editor, and the landing page's capability sections. It is one component idea reused at four scales, which is also why it will be cheap to build.

From the reference: the **alternating band architecture** (full-bleed near-black sections against a light grey desk, 24px panel radius, big confident type, oversized numerals as content), the **light cards on grey ground** inversion, and the restraint — one accent, used sparingly, against a near-monochrome field. What I did *not* take: the coral used decoratively, the rounded-pill chip language, the centred hero.

---

## 1. Palette

Light is authored; dark is derived by remapping the same eight roles. Eight named values, three roles: ground/ink (everything), **time** (one hue), **standing** (one hue + non-colour encodings).

### Core — light

| Token | Hex | Role |
|---|---|---|
| `--ground` | `#F1F0ED` | Page. Warm grey, not cream — oklch chroma 0.004. The desk. |
| `--surface` | `#FBFAF8` | Paper. Cards, panels, the letter, the document viewer. Raised = lighter. |
| `--surface-sunk` | `#E7E5E1` | Wells: input fields, code/quote blocks, media-slot placeholders, the dark band's light inset. |
| `--ink` | `#171715` | Primary text, 17.1:1 on surface. Also the "insurer's claim" border colour. |
| `--ink-muted` | `#605E58` | Secondary text, labels, metadata. 6.3:1 on surface. |
| `--rule` | `#DCD9D3` | Hairlines, card borders, table rules, the margin divider. |
| `--time` | `#9A5B12` | Deadlines only. Deep ochre. 5.7:1 on surface. Never on a large field. |
| `--standing` | `#0C5247` | Solid ground only. Deep teal-green ink. 8.1:1 on surface. |

### Derived tints and the two ramps

| Token | Light | Dark | Use |
|---|---|---|---|
| `--time-ample` | `#605E58` | `#A3A099` | >60 days. **No hue at all.** Plenty of time is not an event. |
| `--time-approaching` | `#B07A2A` | `#D6A75C` | 60–15 days |
| `--time-near` | `#9A5B12` | `#E0A356` | 14–4 days |
| `--time-imminent` | `#7A3E08` | `#F0BE7A` | ≤3 days. Weight 600, ring full, word "days" spelled out. No red, no pulse, no tick. |
| `--time-track` | `#E8DFD1` | `#2E2A23` | Deadline ring track |
| `--standing-tint` | `#DDEAE6` | `#15302C` | Solid-ground node fill |
| `--defeated` | `#7A7872` | `#6E6C66` | Defeated argument ink, 50% strike + 6px diagonal hatch |

### Dark (derived)

`--ground #121211` · `--surface #1C1C1A` · `--surface-sunk #0C0C0B` · `--ink #F2F0EC` · `--ink-muted #A3A099` · `--rule #302F2C` · `--time #E0A356` · `--standing #5FC9B4`

Dark is not an inversion: the desk gets *darker* than the paper, same as light, so panels still read as laid on top. Shadows become `--rule` borders at 1px plus a 1px top highlight.

### Standing palette survives greyscale and all CVD types

Only one hue is used for standing. The other three tiers are encoded without colour:

| Tier | Colour | Border | Marker | Corner |
|---|---|---|---|---|
| Insurer's claim | `--ink` | 1.5px solid | filled square ■ | 2px |
| **Solid ground** | `--standing` | 1.5px solid + 3px left bar | filled circle ● | 10px |
| **Worth adding** | `--ink-muted` | 1.5px **dashed** | hollow diamond ◇ | 10px |
| Defeated | `--defeated` | 1px solid, hatched fill | ✕ | 10px |

Printed in black and white, with the colour channel thrown away, the four tiers are still four distinct objects. That was the constraint and it drove the decision to spend only one hue here.

### Why this is not the cream/serif/terracotta default

`#F1F0ED` is a *grey* at chroma 0.004, not a cream at 0.02 — next to `#F4F1EA` it reads cool. The warm hue in the system appears only on deadlines, where it is a measurement, not a brand colour: there is no ochre button, no ochre underline, no ochre icon. The one saturated colour a user sees on a calm case file is **none**.

---

## 2. Typography

**IBM Plex Sans + IBM Plex Mono for the app, Newsreader for documents.** *(Approved: you kept the semantic split and swapped the serif for a warmer book face.)*

Reasons: tabular lining figures in all three; a 17–19px phone body size with 1.6 leading that stays comfortable past twenty minutes; and a documentary, slightly bureaucratic grain in the sans that reads as *record* rather than *startup*. Newsreader is an optical-size book face with a true italic and moderate stroke contrast — warmer on a long appeal letter than Plex Serif, and still legible on a cracked phone screen. It carries the optical-size axis, so the 17px letter body and the 19px policy quotes are drawn at their own sizes rather than scaled.

The division of labour is semantic, not decorative:
- **Plex Serif** = things the insurer or the user will file: quoted policy language, the generated appeal letter body, physician-letter templates. If it would appear on paper in an envelope, it is serif.
- **Plex Sans** = everything the app says in its own voice: UI, headings, explanations, buttons.
- **Plex Mono** = rule citations, reason codes, claim numbers, dates in dense tables, version stamps. `29 C.F.R. § 2560.503-1(i)` should look like a locator, not like prose.

### Scale (1440 / 390)

| Token | Desktop | Mobile | Face / weight / tracking |
|---|---|---|---|
| `display-xl` | 76 / 76 | 40 / 42 | Sans 600, −0.03em |
| `display-l` | 56 / 60 | 34 / 38 | Sans 600, −0.025em |
| `heading-1` | 36 / 42 | 27 / 33 | Sans 600, −0.015em |
| `heading-2` | 26 / 34 | 21 / 28 | Sans 600, −0.01em |
| `heading-3` | 19 / 26 | 18 / 25 | Sans 600, 0 |
| `body-l` | 19 / 32 | 18 / 30 | Sans 400 — **default reading size** |
| `body` | 16 / 26 | 16 / 26 | Sans 400 — UI default |
| `body-s` | 14 / 21 | 14 / 21 | Sans 400 — metadata |
| `doc` | 18 / 31 | 17 / 30 | **Newsreader 400** — letter + policy quotes |
| `doc-quote` | 18 / 31 | 17 / 30 | **Newsreader 400 italic** |
| `mono` | 13 / 20 | 13 / 20 | Mono 450, 0.01em |
| `mono-s` | 11 / 16 | 11 / 16 | Mono 500 — rules stamp, slot ids |
| `numeral-xl` | 104 / 92 | 60 / 56 | Sans 600, tnum, −0.04em — statistics band, days-remaining |

Measure is capped at **68ch** for `doc`, **74ch** for `body-l`. Nothing in this product is set wider than that, including on a 1440 screen, because the whole point is that it can be read.

No ALL-CAPS tracked eyebrows anywhere. Section labels are `mono-s` in `--ink-muted`, sentence case, sitting on a hairline.

---

## 3. Layout

**Spacing** — 4px base: `1=4 · 2=8 · 3=12 · 4=16 · 5=24 · 6=32 · 7=48 · 8=64 · 9=96 · 10=128 · 11=160`. Vertical rhythm inside documents is a strict 8px lattice so quoted text and its margin note align across the gutter.

**Radius** — `sharp 2` (insurer claim, quote blocks, table cells — anything quoting a source stays square, because paper has corners) · `sm 6` (chips, inputs) · `md 10` (buttons, argument nodes) · `lg 16` (cards) · `xl 24` (full-bleed bands and the workspace shell, from the reference) · `full` (avatars, the deadline ring only).

**Elevation** — three levels, all nearly invisible. `e0` hairline only · `e1` `0 1px 2px rgb(23 23 21 / .05)` + hairline (cards) · `e2` `0 8px 24px -8px rgb(23 23 21 / .12)` + hairline (drawers, popovers, the camera sheet). No glow, no coloured shadow, ever.

**Grid**
- Desktop 1440: 12 col, 80px margins, 24px gutter, 1280 max. Marketing bands go full-bleed; content inside returns to the 1280 container.
- The **margin column** is structural: a 1280 content area splits 7 / 1 / 4 — source column, gutter with the connector rule, annotation column. This split is the house layout, used on the landing capability sections, extraction review, argument graph, and letter editor.
- Mobile 390: single column, 20px margins, 16px gutter. The 7/1/4 split collapses to **quote block, then indented reply** with a 3px left bar and a short connector elbow at the top-left. Same relationship, stacked.
- Tablet 768–1023: 8 col; the margin column drops below its source but keeps the bar and elbow.

**Marketing ↔ workspace**

Same tokens, two different postures.

| | Marketing | Workspace |
|---|---|---|
| Rhythm | Alternating full-bleed bands: light desk → near-black band → light desk. Band radius 24, bands inset 16px from viewport edge so the desk shows around them (reference). | No bands. One continuous desk, panels on it. |
| Density | spacing 9–11 between sections | spacing 5–6 |
| Default text | `body-l` 19px | `body` 16px |
| Chrome | Transparent top bar, product name in Mono, 5 links, one filled button | Fixed 240px left rail (cases, roadmap, arguments, evidence, letter, timeline), collapsing to a bottom bar of 5 items at ≥44px on mobile |
| Shared | The **dossier card**: `--surface` on `--ground`, 16 radius, hairline, a Mono case-id strip across the top. It appears in the landing hero and is the literal case card in the app. Signed-in users landing on marketing see their open case in that card. |

---

## 4. Motion

Framer Motion. Three easings, five durations, and a hard ceiling of **one orchestrated moment per screen**.

```
--ease-exit    cubic-bezier(.4, 0, 1, 1)      --dur-1  120ms  state flips, hovers
--ease-enter   cubic-bezier(.16, .84, .32, 1) --dur-2  180ms  chips, toasts in
--ease-move    cubic-bezier(.65, 0, .35, 1)   --dur-3  260ms  drawers, accordions
                                              --dur-4  420ms  panel/route transitions
                                              --dur-5  700ms  orchestrated only
```

Stagger is 40ms, capped at 8 children; beyond that the group fades as one. Transform and opacity only — nothing animates layout, colour, or a number.

**The orchestrated moment, per screen**

| Screen | Moment | Length |
|---|---|---|
| Landing | Hero dossier card settles onto the desk, case-id strip types once in Mono. | 900ms, once |
| Triage | The track verdict card unfolds downward from the last answer, rule citation fading in 180ms after. | 600ms |
| Extraction wait | Stage list advances — "reading the letter" → "finding the reason codes" → "matching your plan type" — each line crossing to `--ink` as it completes. Honest stages, not a spinner. | real duration |
| Extraction review | Confirming a fact draws the hairline from the fact chip to its source span, then the span's highlight fills left-to-right. | 320ms |
| Roadmap | Timeline draws from the trigger date rightward; deadline rings fill to their arc last, in order. | 800ms |
| **Argument graph** | The insurer's claim sits alone for 400ms. Solid-ground counters arrive and their connectors draw upward into it. Worth-adding tier fades in beneath at 70% then settles. Defeated nodes are already present, struck and hatched — they never animate *out*, because pretending they were never there would be dishonest. **Skip** button present from frame one; the end state is the static diagram. | 1800ms |
| Letter editor | Paragraphs assemble top-down, each with its node badge arriving 80ms behind it. | 1200ms |
| Evidence | Satisfying an item: checkbox fills, row de-emphasises to 70%, and the argument node it feeds pulses its border once. | 300ms |
| Case list | Cards rise 8px in sequence. That is all. | 400ms |

**Never**: a continuously ticking countdown, a pulsing deadline, confetti, a success animation of any kind, a progress bar that lies, spring overshoot on anything carrying a number.

`prefers-reduced-motion: reduce` → every duration becomes 0ms, staggers become simultaneous, the graph renders in its final state with connectors drawn, the extraction stage list still updates as text. No information lives in motion alone.

---

## 5. Principles

1. **Colour is a measurement, not a mood.** Two hues in the entire product. If something is ochre it is about time; if it is teal it holds up. A case with no urgent deadline and no settled arguments is pure grey — and that is correct, because nothing has happened yet.
2. **Everything is quoted or cited.** Every conclusion carries its source in Mono: the rule, the span, the node. This is the honesty requirement and the visual identity at the same time — an advocate's office is full of documents with things written in the margins, not of dashboards.
3. **Urgency is a position, not a volume.** Deadlines are expressed by proximity in the timeline, a filling arc, and an exact date in tabular figures. The loudest a deadline ever gets is a weight change and a darker ochre. Nothing in this product shouts at someone who is ill.
4. **Honest shapes.** Defeated arguments stay on screen, struck through. Confidence levels are shown even when low. The disclaimer is `body-s` at full contrast in the footer and at the head of every generated letter — not 11px grey. Credibility here comes from showing the unflattering parts.
5. **Built for a tired person on a phone.** 18px body on mobile, 44px minimum targets, one-handed reach for primary actions, no hover-only information, full flow completable on a 390px screen with a cracked panel in bad light. Desktop is the expansion, not the origin.

---

## 6. Self-critique, and what I changed

**Caught and killed:**

- *Source Serif 4 + Inter.* My first instinct, and it is the house style of every well-made SaaS site of the last three years. Replaced with the Plex superfamily, where the sans/serif/mono split carries meaning (app voice / filed document / locator) instead of being a tasteful pairing.
- *A semantic colour set of five.* I had green/amber/red/blue/grey for status. Cut to two hues. Red was removed from the product entirely — there is no error red; errors are `--ink` on `--surface-sunk` with a 3px left bar and an explicit sentence. A red error state on top of a denial letter is piling on.
- *Cards in a 3-column grid for the capability sections.* Replaced with the 7/1/4 margin layout, so each capability is demonstrated by the product's own gesture rather than described in a box.
- *A "173 days remaining" hero number as the emotional hook.* It is a stranger's number and it means nothing before upload. The hero now carries the dossier card and the fixed promise; the **statistics band** does the emotional work, as the brief asks — under 0.2% appeal, roughly half who do win, set in 104px tabular numerals on the dark band.
- *Rounded-pill everything.* Anything quoting a source is now square-cornered (radius 2). Pills are reserved for status, where the shape says "this is a label, not a document".
- *A progress spinner during extraction.* Replaced with named stages. A spinner during the one moment the user is most anxious is the worst place in the product to be vague.

**Three things I know are arguable:**

1. ~~Plex Mono as a third face.~~ **Resolved:** you kept the split. Plex Sans + Plex Mono are one superfamily; Newsreader is the document voice.
2. ~~The deadline ochre sits near terracotta.~~ **Resolved:** ochre ramp approved, with no hue at all above 60 days.
3. **One** standing hue, with the other three tiers carried by border style and marker shape. This is the strongest accessibility position available and makes printing trivial, but it means "worth adding" is visually quieter than a colour-coded system would make it. I think that is right — the tier *is* the optional one — but it is a choice, not a given.

**Scope (approved):** core flow first — landing, triage, case list, upload, extraction review, roadmap, argument graph, evidence, letter editor. Pricing/legal, auth, timeline, escalation, settings, system states, dialogs and emails follow in a second build.

---

## 7. Demo case used across all screens (Pass 2)

So every screen tells one coherent story rather than lorem-ipsum state. Defaults, overridable:

> **M. Okonkwo · employer-sponsored plan (ERISA, self-funded) · Claim #CLM-4471902 · denied 14 Sep 2026.** Reason code `CO-50` — "not medically necessary." Requested treatment: continued infusion therapy after step-therapy failure. Internal appeal deadline **22 Mar 2027 — 168 days**. Three solid-ground arguments, two worth adding, one defeated.

---

## 8. Pass 2 deliverable order

B. `tokens.css` + `tailwind.theme.ts` (generated from one source list so they cannot drift)
C. Screens — landing, triage, pricing, legal · auth, case list, upload, extraction review, roadmap, **argument graph**, evidence, letter editor, timeline, escalation, settings · system states, dialogs, emails, 404/500. Each at 1440 and 390, light and dark, interactive.
D. `components.md` — 24 components, variants, states, props
E. `media-manifest.md` — 18 slots with intrinsic sizes
F. `motion.md`
