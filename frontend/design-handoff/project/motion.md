# motion.md

Framer Motion. Three easings, five durations, one orchestrated moment per screen. Every
value below is a token from `tokens.css`; nothing is authored inline.

## Tokens

```ts
export const ease = {
  exit:  [0.4,  0,    1,    1   ],  // --ease-exit   leaving, collapsing
  enter: [0.16, 0.84, 0.32, 1   ],  // --ease-enter  arriving, expanding
  move:  [0.65, 0,    0.35, 1   ],  // --ease-move   travelling, reordering
} as const

export const dur = {
  1: 0.12,  // state flips, hover, pill changes
  2: 0.18,  // chips, toasts, tooltips in
  3: 0.26,  // drawers, accordions, panels
  4: 0.42,  // route and view transitions
  5: 0.70,  // orchestrated sequences only
} as const
```

Stagger is `0.04` with `delayChildren: 0.06`, capped at 8 children. Past 8, the group
fades as one — a nine-item stagger is a wait, not a flourish.

**Only `transform` and `opacity` animate.** Never `height`, `width`, `top`, `color`, or a
displayed number. Accordions animate `grid-template-rows: 0fr → 1fr`, which the compositor
handles without layout thrash. Counters set their value immediately; a number that rolls up
is a number you cannot read.

## The landing page — one gesture per section, none reused

The landing page is scroll-driven, not time-driven: every reveal runs on a native CSS
view-progress timeline, so the animation is tied to the reader's position rather than to a
clock. Nothing waits for an observer, nothing can desynchronise, and scrubbing back up
re-runs it. Five `animation-range` offsets provide the stagger within a section.

| # | Section | Gesture | Why this one |
|---|---|---|---|
| 01 | Hero | Each headline line rises out of its own clipped box (`aa-lineup`), 120ms apart, over a 14s ken-burns push on the background plate. Sub, buttons and the meta strip lift after. | The only time-based sequence on the page, because the hero is above the fold. A line emerging from a hard edge is a typesetting gesture, not a UI one. |
| — | Promise marquee | Continuous horizontal scroll, 46s linear, infinite (`aa-marquee`). | The one thing on the page that never stops. It is a ticker of fixed promises, so it behaves like a ticker. |
| 02 | Statistics | Each column's top rule draws left to right, then the numeral rises out of a clipped box (`aa-countup`). | The rule arrives before the number it measures. |
| 03 | How it works | The horizontal spine draws across the full width (`aa-drawright`, range `entry 0% → cover 86%`), stations lift, and each station dot pops as the line reaches it. | The only section whose animation is a single continuous line across three columns rather than three parallel reveals — which is exactly what stops it reading as three cards. |
| 04 | What it does | The quote's 2px clay rule draws downward (`aa-drawdown`), the media wipes in from the left (`aa-wiperight`), and the answer column nudges in from its margin (`aa-nudge`). | Three different directions in one row, mirroring the left-to-right argument. |
| 05 | Who uses it | Portraits wipe open horizontally, staggered by each column's own vertical offset. | The columns start at different heights, so the stagger is a consequence of the composition rather than an arbitrary delay. |
| 06 | Pricing | Each column's top rule draws right; the featured column's rule is 3px clay and draws with the others. | No cards to animate, so the rules carry it. |
| 07 | Questions | Each row's hairline sweeps right as it enters. | The thinnest possible gesture for the densest part of the page. |
| 08 | Closing call | The headline rises out of its clip box, matching the hero. | Bookends the page with the same move, which is the only intentional repeat. |

## The orchestrated moment, per authenticated screen

Exactly one per screen. Everything else is a 120–260ms state change.

| Screen | Moment | Total | Detail |
|---|---|---|---|
| Landing | Hero dossier card settles onto the desk | 900ms | Card: `y 14 → 0`, `opacity 0 → 1`, `dur-4`, `ease-enter`. The case-id strip types once in mono at 28ms/char after a 420ms delay. Does not repeat on scroll-back. |
| Triage | Track verdict unfolds | 600ms | The verdict card scales `0.98 → 1` and fades in from the position of the last answered option. Each of the three result cards follows at 40ms stagger. The rule citation fades in 180ms after its card, so the claim lands before its proof. |
| Extraction (working) | Stage list advances | real duration | Each stage's ring fills `scale 0 → 1` over `dur-3` as it completes, and its label crosses from `--ink-muted` to `--ink`. Honest stages, no synthetic pacing. If a stage takes longer than expected the label changes to say so. |
| Extraction (review) | Confirming a fact | 320ms | The connector hairline draws from the fact chip to its source span (`scaleX 0 → 1`, `ease-move`, 180ms), then the span's highlight fills left to right (140ms). The left bar changes to `--standing` in `dur-1`. |
| Roadmap | Timeline draws | 800ms | Steps rise `y 10 → 0` at 60ms stagger, `ease-enter`. Each deadline ring then fills to its arc in order, 220ms each, 80ms apart. Rings fill once and hold. |
| **Argument graph** | The refutation assembles | 1800ms | See the full sequence below. |
| Letter editor | Paragraphs assemble | 1200ms | Top-down, `y 8 → 0` + fade, 90ms stagger, `ease-enter`. Each node badge arrives 80ms behind its paragraph, so the reader sees the sentence before its justification. |
| Evidence | Satisfying an item | 300ms | Box fills (`dur-1`), row drops to 78% opacity (`dur-3`), and the argument node that item feeds pulses its border once: `box-shadow` spread `0 → 3px → 0` over 300ms. The pulse fires even if the node is off-screen — it is a state change the user will see on return, not an attention-grab. |
| Case list | Cards rise | 400ms | `y 8 → 0`, 50ms stagger, `ease-enter`. That is all. |
| Rule drawer | Slide in | 260ms | `x 100% → 0`, `ease-move`; scrim fades `dur-2`. Focus moves to the drawer heading on arrival and returns to the trigger on close. |

## The argument graph sequence

The hardest moment and the one most at risk of becoming theatre. It is a short explanation,
not a reveal.

```
0ms      ClaimCard fades up (y 12 → 0, dur-4, ease-enter)
400ms    — held alone. The insurer's reason is the only thing on screen.
400ms    ArgumentBus connectors draw: centre drop scaleY 0 → 1 (180ms),
         horizontal span scaleX 0 → 1 from centre (220ms),
         lane ticks scaleY 0 → 1 (120ms each)
700ms    Solid-ground lane header fades in (dur-2)
760ms    Solid nodes rise, 110ms stagger — A1, A2, A3
1180ms   Worth-adding lane header and nodes enter at 70% opacity,
         then settle to 100% over dur-3
1620ms   Left-out section fades in (dur-2)
1800ms   done
```

Defeated nodes are **present from the start of their section and never animate out.**
Animating a defeated argument away would stage a small victory the product has not earned,
and would hide the fact that it was considered.

A **Skip** control is in the DOM from frame one, focusable, 44px, labelled "Show it all".
Pressing it jumps to the end state instantly. The sequence plays once per case; returning to
the screen shows the static diagram.

## What never animates

- A countdown. Days remaining is set, not counted.
- A deadline. No pulse, no shake, no colour transition, no attention loop. The most urgent
  state in the product is also one of its stillest.
- An outcome. No confetti, no checkmark burst, no celebratory scale, no sound.
- A spinner. Named stages replace every one.
- A progress bar that moves without a corresponding real event.
- Spring overshoot on anything carrying a number or a date. `ease-enter` only.

## Reduced motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
  }
}
```

With `useReducedMotion()` in Framer Motion, every `transition` resolves to `{ duration: 0 }`
and staggers to 0. Specifically:

- The argument graph renders in its final state with all connectors drawn.
- The extraction stage list still advances — the text changes are information, not motion,
  and they stay.
- Deadline rings render at their final arc.
- Drawers and dialogs appear and disappear without travel; focus management is unchanged.

**No information lives in motion alone.** Every animated transition has a static end state
that carries the same meaning, which is also why the whole product screenshots correctly and
prints correctly.

## Implementation notes

- One `MotionConfig` at the app root carries `reducedMotion="user"` and the default
  transition `{ ease: ease.enter, duration: dur[3] }`.
- Orchestrated sequences use a single parent `variants` object with
  `staggerChildren` — never `setTimeout` chains, which desynchronise under load on the
  low-end phones a lot of these users have.
- `layout` animations are disabled globally. Nothing in this product reflows for effect.
- Route transitions: outgoing `opacity → 0` at `dur-2` with `ease-exit`, incoming
  `opacity 0 → 1, y 6 → 0` at `dur-4` with `ease-enter`. No horizontal slide — it implies a
  linear wizard, and this product lets you move around the case freely.
