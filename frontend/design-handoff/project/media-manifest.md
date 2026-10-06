# media-manifest.md

Every deferred asset slot. `MediaSlot` holds the ratio exactly, so dropping the real asset
in changes no layout. Intrinsic size is the minimum pixel size to supply; ship 2× for
raster unless noted.

Nothing in this list may depict a win: no celebration, no cheque, no thumbs-up, no gavel,
no stethoscope-and-clipboard stock imagery. Photography is quiet, warm-grey, documentary.

| # | Slot id | Page | Type | Ratio | Intrinsic | What it depicts |
|---|---|---|---|---|---|---|
| 1 | `hero-bg` | Landing — hero, full-bleed background | Video, muted loop, ≤16s. **`fill` mode** | fills the 720px hero frame (no fixed ratio) | 2560×1440 | Slow documentary footage: a person at a kitchen table opening a denial letter, late afternoon light. Must hold up under a heavy forest scrim at 34–93% — low contrast, no fast motion, nothing legible in frame. A still at the same size is an acceptable substitute. |
| 2 | `trust-strip` | Landing — trust strip | Image strip, SVG preferred | 8 / 1 | 960×120 | Security and privacy marks — encryption, data handling, the plain-language privacy link. Monochrome `--ink-muted`, no badge shields. At this ratio the slot renders its **tight** placeholder (one inline label, no corner stamps). |
| 3 | `stat-backdrop` | Landing — statistics band | Image, sits at 14% opacity behind the numerals. **`fill` mode** | fills the band (no fixed ratio) | 2100×900 | A very quiet backdrop: stacked paper edges in raking light, near-abstract. Must read as texture at 14%, never as a photograph competing with the figures. |
| 4 | `feature-roadmap` | Landing — capability 1 | Image (product shot) | 4 / 3 | 1200×900 | The procedural roadmap with its four steps and deadline rings, light theme, desktop. |
| 5 | `feature-graph` | Landing — capability 2 | Image (product shot) | 4 / 3 | 1200×900 | The argument graph showing the claim card, the solid-ground lane and the worth-adding lane side by side. |
| 6 | `feature-letter` | Landing — capability 3 | Image (product shot) | 3 / 4 | 900×1200 | A generated appeal letter page with node badges in the margin. Body text legible at 50% scale. |
| 7 | `feature-evidence` | Landing — capability 4 | Video, muted loop, ≤8s | 1 / 1 | 900×900 | Evidence checklist items being satisfied one at a time, with the supporting argument reference visible on each row. |
| 8 | `persona-1` | Landing — who uses it | Image, landscape crop | 4 / 3 | 1024×768 | A person at a kitchen table with a letter, mid-afternoon. Unposed, no eye contact with camera, no distress acting. Sits at the top of a card; keep the subject in the lower two-thirds. |
| 9 | `persona-2` | Landing — who uses it | Image, landscape crop | 4 / 3 | 1024×768 | A person managing a chronic condition at a laptop, a folder of prior correspondence beside them. Competent, not weary. |
| 10 | `persona-3` | Landing — who uses it | Image, landscape crop | 4 / 3 | 1024×768 | A caregiver on a phone in a waiting room, handling it for someone else. Phone screen not legible. |
| 11 | `empty-cases` | Case list — empty state | Illustration, SVG | 4 / 3 | 640×480 | A closed folder resting on a desk. Line weight 1.5px at `--rule`, two tones maximum, no faces, no mascot. |
| 12 | `upload-icon` | Upload — drop zone | Illustration, SVG | 1 / 1 | 512×512 | A page being placed into a folder. Same line vocabulary as #11. |
| 13 | `camera-guide` | Upload — phone guidance panel | Image | 3 / 4 | 900×1200 | A denial letter framed correctly in a phone camera, with corner guides visible. Shows the right distance and the right light. |
| 14 | `doc-scan` | Extraction review — document viewer | Image, one per page | 17 / 22 | 1700×2200 | Page of the denial letter with extracted spans highlighted. US Letter ratio exactly. Supply three pages: `doc-scan-1/2/3`. Must be a realistic synthetic letter — never a real member's document. |
| 15 | `graph-legend` | Argument graph — first-run overlay | Illustration, SVG | 3 / 2 | 900×600 | The three tier markers (`●` `◇` `✕`) with their border treatments and one line each. Shown once per case, dismissible, reachable afterwards from the header. |
| 16 | `letter-preview` | Letter editor — export dialog | Image | 17 / 22 | 1700×2200 | The letter as it will print on US Letter, margins visible, node badges absent. |
| 17 | `physician-template` | Evidence — physician letter card | Document, PDF + DOCX | 17 / 22 | — | The downloadable template: letterhead space, the four required points as prompts, signature and date block. Supplied as files, not an image. |
| 18 | `og-card` | All pages — social share | Image | 1200 / 630 | 1200×630 | Wordmark in mono, the fixed line "Your denial, formally refuted.", `--ground` field, one dossier card edge. No faces, no statistics. |

## The three placeholder modes

`MediaSlot` picks its own presentation so a placeholder never collides with the layout
around it:

| Mode | When | Renders |
|---|---|---|
| **roomy** (default) | ratio narrower than 5:1 | Sunk fill, hairline border, hatch, centred kind pill + description, `slotId` and `intrinsic` pinned to the bottom corners |
| **tight** | ratio 5:1 or wider — too short for stacked text | One inline marker + label, no corner stamps |
| **fill** | `fill` prop set — the slot is a background layer | `position:absolute; inset:0`, no aspect ratio, hatch only, with a single corner line reading `slotId · kind · intrinsic`. No centred caption, so nothing can land on the headline above it. |

Use **fill** for any slot behind type (#1, #3). Everything else sizes itself.

## Fallback behaviour

If an asset is absent at build time the slot renders as designed. That state is intentional
and shippable: it reads as a reserved space in a document, not as a broken image. Alt text
for every slot is the `label` string in this table verbatim; decorative slots (#1, #3) take
`alt=""` and `aria-hidden`.

## Ratio reference

`17 / 22` is US Letter (8.5 × 11in). Every document-facing slot uses it so scans, previews
and exports share one geometry.
