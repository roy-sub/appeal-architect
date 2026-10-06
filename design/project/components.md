# components.md

Every component in Appeal Architect. Names are the React component names; props are the
implementable surface. Values reference tokens from `tokens.css` / `tailwind.theme.ts` —
no raw hex, no magic numbers.

Conventions used throughout:
- `tone` never carries meaning alone. Every tone is paired with a border style, a marker
  glyph, or a word.
- Every interactive element is at least 44px on its smallest axis.
- Focus is `outline: 2px solid var(--focus); outline-offset: 2px` from the global
  `:focus-visible` rule. No component overrides it.
- Motion durations and easings come from the `--dur-*` / `--ease-*` tokens only.

---

## 1. Primitives

### Button
`variant` · `size` · `disabled` · `loading` · `fullWidth` · `onClick` · `children`

| variant | fill | border | text | use |
|---|---|---|---|---|
| `primary` | `--ink` | none | `--ground` | one per view, the thing to do next |
| `secondary` | `--surface` | 1px `--rule` | `--ink` | the alternative |
| `quiet` | transparent | 1px `--rule` | `--ink-muted` | back, cancel, skip |
| `inline` | none | none | `--ink`, underlined | inside running prose |

| size | min-height | padding | radius | type |
|---|---|---|---|---|
| `sm` | 44px | 9/13 | `--r-sm` | body-s 14 |
| `md` | 46px | 11/16 | `--r-md` | body 16 |
| `lg` | 48px | 14/22 | `--r-md` | body 16/500 |

`sm` is visually small but keeps the 44px box — the padding does the work, not a shrunken
target. `loading` replaces the label with the label plus a trailing `…`, never a spinner,
and keeps the button's width so nothing jumps. Disabled is `opacity .45` **plus**
`cursor: not-allowed` **plus** an `aria-disabled` and a reason in the adjacent helper text;
a greyed button with no stated reason is a dead end.

### Pill
`tone: 'standing' | 'add' | 'defeated' | 'ink' | 'plain'` · `children`

Mono 11px, `--r-sharp`, 4/9 padding. `add` is the only dashed one. Non-interactive by
default; `onRemove` turns it into a 44px-tall chip with an `✕`.

### Field
`label` · `value` · `onChange` · `hint` · `error` · `multiline` · `inputMode`

Label is mono-s above the control, never a placeholder — placeholders vanish exactly when
a tired person needs them. Control: `--surface`, 1.5px `--ink` border, `--r-sm`, 46px min.
**Error state uses no red.** The border thickens to 2px `--ink`, a 3px `--ink` bar appears
on the left, and the message sits below in `body-s` at full `--ink` contrast, phrased as
an instruction: "Enter the date printed on the letter, not today's date."

### Rule
A 1px `--rule` hairline, optionally with a mono-s label flushed left and the line filling
the remainder. This is the only section divider in the product.

### Stat
`value` · `label` · `note`. `numeral-xl` tabular figures over a `--band-rule` top border.
Used only in the marketing statistics band.

### MediaSlot
`slotId` · `ratio` · `kind` · `label` · `intrinsic` · `fit`

The deferred-asset placeholder. `--surface-sunk` fill, 1px `--rule` border, a 45° hairline
cross at 6% opacity, the `kind` in mono-s centred, the `label` in `body-s` below it, and
`slotId` / `intrinsic` in mono-s pinned to the bottom corners. It holds its aspect ratio
exactly, so dropping the real asset in changes nothing about the layout. Documented per
instance in `media-manifest.md`.

---

## 2. Time

### DeadlineRing
`days` · `total` · `size: 48 | 56 | 64 | 76 | 96`

A conic-gradient arc on a `--time-track` ring with a `--surface` hole. The arc shows
*elapsed* proportion, so it fills as the deadline approaches. Inside: the day count in
tabular figures, "DAYS" in mono-s beneath.

| days remaining | token | weight | word shown beside it |
|---|---|---|---|
| > 60 | `--time-ample` (no hue) | 500 | on track |
| 60–15 | `--time-approaching` | 500 | approaching |
| 14–4 | `--time-near` | 600 | close |
| ≤ 3 | `--time-imminent` | 600 | act now |
| passed | `--defeated` | 600 | window closed — see options |

The ring never animates after its one entrance fill. It never pulses, never ticks, and
never counts down live. The exact date is always printed next to it — the ring is the
glance, the date is the fact.

### DeadlineBanner
`date` · `days` · `total` · `action`
Card-level composition: ring + "Next thing due" + the sentence + a secondary button.
Carries the reminder schedule as reassurance: "We will remind you at 30, 14, 7, 3 and 1
days, and again the morning it is due."

---

## 3. Document surfaces

### SourceQuote
`source` · `children` · `size`

The house gesture. Mono-s source line, then `--font-doc` italic at `doc` size behind a
1.5px `--ink` left rule with 16–18px of padding. Square corners. Used for insurer
language, plan language, and regulation text. Never used for the product's own voice.

### MarginNote
`children` · `tier`
The right-hand half of the 7/1/4 split. On desktop it sits in the annotation column with
a hairline connector running to the quote. Below 1024 it drops under the quote and keeps a
3px left bar — `--standing` where the note is a conclusion, `--rule` where it is commentary.

### FactRow
`fact` · `state` · `confidence` · `span` · `onConfirm` · `onEdit` · `onReject`

Key in mono-s, value in `body-l` 500. Left border 3px, radius `2px 10px 10px 2px` — square
on the source side, rounded on the app side, which is the whole metaphor in one shape.

| state | left bar | pill |
|---|---|---|
| `pending` | `--time` | "Needs a look" |
| `confirmed` | `--standing` | "Confirmed" |
| `edited` | `--standing` | "Edited by you" |
| `rejected` | `--defeated` | "Rejected" |

`confidence: low` prints "The scan is unclear here" in `--time` — the only place outside a
deadline where the time hue appears, because low confidence is a thing the user must spend
time on. Editing swaps the value for a `Field` plus Save / Cancel; nothing is destructive
without the swap.

### DocViewer
`pages` · `page` · `highlights` · `onHighlightClick`
MediaSlot per page plus a well containing the currently selected span as a `SourceQuote`.
Selecting a `FactRow` scrolls the span into view and fills its highlight left to right;
selecting a highlight selects the fact. Sticky on desktop, stacked above the facts on mobile.

### LetterSheet
`paragraphs` · `activeId` · `onSelect`
`--surface`, radius `--r-sharp`, 44/56 padding on desktop. A mono-s address block, the
salutation, then `Paragraph` children, then the signature block, then the disclaimer at
`body-s` full contrast. Prints at US Letter with 1in margins; the node badges are
`display: none` in print.

### Paragraph
`ref` · `text` · `active` · `onSelect`
Serif `doc`, with a node badge (`A2`, or `procedural` for the ones no argument produced)
above it. Active: `--standing-tint` fill, 2px `--standing` left border. Selecting a
paragraph selects its argument node everywhere else in the app.

---

## 4. The argument graph

### ClaimCard
`code` · `text` · `meta`
The insurer's reason. 1.5px solid `--ink`, radius `--r-sharp`, a filled `--ink` square
marker, the quoted sentence in serif italic, the provenance in mono-s under a hairline.
Always the first element, always alone. It is the only node the user did not choose.

### ArgumentNode
`tier: 'solid' | 'add' | 'defeated'` · `ref` · `title` · `assert` · `status` · `reply` ·
`verdict` · `why` · `needs` · `active` · `onSelect`

| tier | border | left bar | marker | fill | title |
|---|---|---|---|---|---|
| `solid` | 1.5px solid `--standing` | 3px `--standing` | `●` | `--surface` | `--ink` |
| `add` | 1.5px **dashed** `--ink-muted` | — | `◇` | `--surface` | `--ink` |
| `defeated` | 1px solid `--defeated` | — | `✕` | 6px diagonal `--stripe` hatch | `--defeated`, struck through |

Four distinguishing signals per tier (border weight, border style, marker glyph, fill), of
which colour is one. Printed greyscale or read with any form of colour blindness, the three
tiers remain three.

Active: `box-shadow: 0 0 0 2px var(--focus)`. On mobile the active node expands in place to
show reply / verdict / why / needs. On desktop the same content fills `ArgumentDetail`.

### ArgumentLane
`tier` · `count` · `nodes`
A tier header — top border matching the tier's border style, marker, name, count, and one
sentence of plain-language explanation — above a stack of nodes. The explanations are fixed
copy:
- Solid ground: "These stand up to whatever the insurer answers. Your letter leads with them."
- Worth adding: "The insurer has a fair answer to each of these. Useful as extra weight, not as your main point."
- Left out: "We checked this one and it does not hold. It stays visible so you know it was considered."

### ArgumentDetail
`node`
Desktop-only sticky panel: tier pill, ref, title, assertion, the insurer's possible reply in
a `--surface-sunk` well, the verdict line, the reasoning, the evidence needed, and a link to
the evidence list. The verdict is a sentence, never an icon: "Does not defeat it" /
"They can knock this one back" / "Left out".

### ArgumentBus
Desktop connector between `ClaimCard` and the lanes: a centre drop, a horizontal span, and
one tick per lane coloured to the lane's tier. Hidden below 1024, where the left bars and
stacking order carry the relationship instead. `aria-hidden` — it is decoration over
structure that already exists in the DOM order.

---

## 5. Case and procedure

### CaseCard
`insurer` · `claim` · `reason` · `stage` · `date` · `days` · `total` · `onOpen`
Ring, then insurer / reason / stage pills, then the next deadline. The whole card is one
button. Stacks to a column below 1024.

### RoadmapStep
`n` · `title` · `who` · `date` · `days` · `need` · `rule` · `state` · `onOpen`
Step number in mono-s, a `who` pill ("You file" / "They answer" / "You request" /
"Reviewer decides"), a ring, the date in tabular figures, the state line, what the step
needs, and the citation under a hairline. The current step gets a 1.5px `--ink` border;
future steps stay at 1px `--rule` and read "Starts after step 01". Row on desktop, column
on mobile.

### RuleDrawer
`step` · `onClose`
Right-side sheet, 460px desktop / full-width mobile, `--e2`. Contains: the due date at
`heading-1` scale, how the date was worked out in plain language, the regulation text as a
`SourceQuote` in a well, what the step needs, and the standing caveat — "Deadlines are our
best reading of your plan and the regulations. Check the date against your own letter
before you rely on it." Scrim is `--overlay`; Escape and scrim-click both close; focus is
trapped and returns to the trigger.

### EvidenceItem
`title` · `why` · `how` · `state` · `onToggle`
A 44px checkbox control (18px visual box inside a 44px hit area), the item, how to actually
get it in one sentence, and "Supports A1 A2" in mono-s under a hairline. States: `have`
(`--standing` fill, row to 78% opacity), `missing`, `progress` ("Requested"), `optional`
(dashed box, "Optional" pill). Satisfying an item pulses the border of the argument node it
feeds, once.

### PhysicianLetterCard
The four required points, numbered in mono-s, plus Copy and Download actions, plus the
honesty line: "We do not write this letter for the doctor. A reviewer can tell when a
physician letter was not written by a physician."

---

## 6. Shell and navigation

### AppShell
Desktop: 252px left rail (sticky, `--ground`, 1px `--rule` right border) + main column.
Mobile: main column + sticky bottom bar of 5 items at 52px each. The rail carries the rules
stamp — "Rules current as of 5 Oct 2026 · version 2026.10.1" — pinned to its bottom.

### CaseHeader
Sticky, `--ground`, hairline bottom. Case title, mono-s claim/date/code line, and the next
deadline as an `--ink` pill. Present on every authenticated screen so the deadline is never
more than a glance away.

### MarketingNav / MarketingFooter
Transparent nav, wordmark in mono, three links, one primary button. Footer is a `--band`
block with `--r-xl` top corners carrying the full disclaimer at `body-s` full contrast and
the rules version stamp.

### QuestionStep (triage)
Progress line, question at `heading-1`, one line of help, then option buttons at 60px min
with a 16px square indicator. Answering advances automatically; Back is always present and
never destructive. The right-hand panel lists the three things the check will produce and
fills them in as they become known.

### TrackVerdict
The triage result: track card with its regulation, deadline card with the ring and the
counting method, and a worth-it card that states the honest position and then says "That is
not a prediction about your case. Nobody can give you one."

### StageList (extraction)
Named stages, each with a `--standing` ring that fills as it completes, the active one at
weight 500. Replaces every spinner in the product. Carries "You can close this page. We
will email you when it is ready, and the case keeps its place."

### EmptyState
MediaSlot illustration at 120px, a `heading-2`, one sentence of what to do, one primary
button. Never a slogan, never an exclamation mark.

---

## 7. Global rules these components obey

**No red anywhere.** Errors, rejections and defeated arguments use `--ink` or `--defeated`
with a border or bar, plus words.

**No outcome language.** No component has a success state that implies winning. The letter
exports; the evidence completes; the deadline is met. Nothing says you will prevail.

**No hover-only information.** Every tooltip has a tap target and persists until dismissed.

**Reduced motion.** All `--dur-*` resolve to `0.001ms` under `prefers-reduced-motion`. The
argument graph renders in its final state with connectors drawn; the stage list still
advances as text.

**Touch.** 44px minimum on every control. The bottom bar is 52px plus safe-area inset. The
primary action on every mobile screen sits in the lower half of the viewport.
