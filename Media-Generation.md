# Media generation

Thirteen assets. Every one has a slot already reserved in the code, holding its
exact aspect ratio — dropping a file in changes **no layout**. Until a file
exists the slot renders its designed placeholder, which is intentional and
shippable, so nothing here blocks launch.

Save each file at the exact path given. The filename is what the code looks for.

---

## The list

| # | Slot | Type | Page | Section |
|---|---|---|---|---|
| 1 | `hero-bg` | Video | Landing | Hero, full-bleed background |
| 2 | `stat-backdrop` | Image | Landing | Statistics band, behind the numerals |
| 3 | `feature-roadmap` | Image | Landing | Capability 1 — deadlines and their rules |
| 4 | `feature-graph` | Image | Landing | Capability 2 — solid ground, worth adding |
| 5 | `feature-letter` | Image | Landing | Capability 3 — every paragraph backed by a rule |
| 6 | `feature-evidence` | Video | Landing | Capability 4 — the evidence list |
| 7 | `persona-1` | Image | Landing | Who uses it — first time |
| 8 | `persona-2` | Image | Landing | Who uses it — been here before |
| 9 | `persona-3` | Image | Landing | Who uses it — for someone else |
| 10 | `empty-cases` | Illustration | Case list | Empty state |
| 11 | `upload-icon` | Illustration | Documents | Drop zone |
| 12 | `camera-guide` | Image | Documents | Photographing a letter panel |
| 13 | `og-card` | Image | All pages | Social share preview |

---

## House rules — apply to every prompt below

These are not taste. They are what keeps the product credible to someone who is
frightened and deciding within thirty seconds whether this is a scam.

- **Nothing may depict a win.** No celebration, no cheque, no thumbs-up, no
  handshake, no raised fist, no confetti. The product never implies an outcome.
- **No legal or medical iconography.** No gavels, scales, shields, stethoscopes,
  clipboards or white coats.
- **No stock-photo emotion.** Nobody acting distressed, nobody beaming. Unposed,
  no eye contact with the camera.
- **No blue.** Blue reads "hospital portal", which is precisely what this design
  is not. Warm paper and deep forest green, one clay-orange accent:
  `#F2EDE4` ground · `#FFFCF7` surface · `#1C1A17` ink · `#14453A` forest ·
  `#C85A33` clay.
- **No text in any image** except #13, which specifies its wording exactly.
  Generated lettering is always slightly wrong and it is the first thing that
  reads as fake.
- **Documentary, warm, quiet.** A reportage photographer in somebody's kitchen in
  late afternoon, not a brochure.

---

## 1. Hero background

**Type:** Video (muted, loops, ≤ 16s, ≤ 4 MB) · a still is an acceptable substitute
**Aspect ratio:** 16:9 — 2560 × 1440
**Save as:** `frontend/public/media/hero-bg.mp4`
**Also save a still:** `frontend/public/media/hero-bg.jpg` (same framing, 2560 × 1440)

> This sits under a forest-green scrim at 34–93% opacity with white headline text
> over it. It must be low contrast, with no legible detail and no fast motion.

```
Slow documentary footage, late afternoon in a modest home kitchen.
Over-the-shoulder framing, shallow depth of field. A person in their fifties
sits at a wooden table holding a single sheet of printed paper, reading it. A
mug, reading glasses and an opened envelope rest on the table. Warm low sun
through a window to one side, dust visible in the light. Muted warm palette of
oatmeal, faded terracotta and worn wood. Almost no camera movement — a very slow
push in. Nothing written on the paper is legible. The person is calm and
absorbed, not distressed. Grainy 35mm film feel, soft shadows, no blue colour
grading. Nobody looks at the camera. 16:9.
```

---

## 2. Statistics band backdrop

**Type:** Image
**Aspect ratio:** 21:9 — 2100 × 900
**Save as:** `frontend/public/media/stat-backdrop.jpg`

> Renders at **14% opacity** behind large numerals. It must read as texture,
> never as a photograph competing with the figures.

```
Near-abstract macro photograph of the stacked edges of a thick pile of paper
documents, shot almost edge-on in raking low light so each sheet edge catches a
thin highlight. Warm cream and pale ochre tones. Very shallow depth of field,
most of the frame falling soft. No text, no hands, no visible page content.
Quiet and archival, like a records room. High key, low contrast. 21:9.
```

---

## 3. Feature — the roadmap

**Type:** Image (product shot)
**Aspect ratio:** 16:10 — 1600 × 1000
**Save as:** `frontend/public/media/feature-roadmap.png`

```
A clean product screenshot mockup of a web application, light theme, on a warm
off-white background (#FFFCF7). It shows a horizontal procedural timeline of
four numbered steps, each a card with softly rounded corners. Each card has a
small circular progress ring in deep forest green (#14453A), a bold date, and
two short lines of grey text beneath. A thin hairline rule runs behind the row
connecting the steps. Clean humanist sans-serif typography. Generous whitespace,
strict Swiss-grid alignment. Palette strictly warm cream, deep green and
charcoal, with one small orange accent button. No browser chrome, no cursor, no
photographic elements. Crisp and flat — no gradients, no glass effects, no
drop shadows. 16:10.
```

---

## 4. Feature — the argument graph

**Type:** Image (product shot)
**Aspect ratio:** 16:10 — 1600 × 1000
**Save as:** `frontend/public/media/feature-graph.png`

> This is the product's centrepiece. Worth generating several times and picking
> the best.

```
A clean product screenshot mockup of a web application, light theme on a warm
off-white background. At the top centre sits a single card with sharp 2px
corners and a 1.5px solid charcoal border, representing a claim. Thin hairline
connector lines descend from it to two columns of cards below. The left column's
cards have a solid deep-forest-green border with a thicker 3px green bar down
the left edge and a small filled circle marker. The right column's cards have a
dashed grey border and a small outlined diamond marker. Each card contains one
short bold line and two lines of smaller grey text. Clean humanist sans-serif,
generous whitespace, strict alignment. Warm cream, deep green and charcoal only.
No browser chrome, no photographs, no glow, no 3D. 16:10.
```

---

## 5. Feature — the letter

**Type:** Image
**Aspect ratio:** 4:5 — 1200 × 1500
**Save as:** `frontend/public/media/feature-letter.png`

```
A single page of a formal business letter on warm white paper, photographed flat
from directly above in soft even light. Dense justified body text set in a
readable book serif — legible as typography but the individual words indistinct
and unreadable. Generous one-inch margins. In the left margin beside each
paragraph sits a small monospace reference tag in muted grey. A signature line
and date block at the foot. The page rests on a warm cream surface with a barely
visible shadow at its edge. No letterhead logo, no readable names, no addresses.
Calm, precise, archival. 4:5 portrait.
```

---

## 6. Feature — evidence being satisfied

**Type:** Video (muted, loops, ≤ 8s, ≤ 2 MB)
**Aspect ratio:** 16:10 — 1600 × 1000
**Save as:** `frontend/public/media/feature-evidence.mp4`

```
A short screen-recording style animation, light theme on a warm off-white
background. A vertical checklist of five rows, each with a small square checkbox
on the left, a bold label, and a line of smaller grey text. One at a time, from
the top, each checkbox fills with deep forest green and its row settles very
slightly in opacity. Beneath each satisfied row a small monospace reference
appears. Movement is calm and slow — roughly one row every 1.2 seconds. No
cursor, no click effects, no confetti, no tick-burst animation. Clean humanist
sans-serif, generous spacing. 16:10.
```

---

## 7. Who uses it — first time

**Type:** Image
**Aspect ratio:** 4:5 — 1000 × 1250
**Save as:** `frontend/public/media/persona-1.jpg`

```
Documentary photograph, mid-afternoon. A person in their forties sits at a
kitchen table in a modest home, holding a single sheet of printed paper in one
hand and looking at it with quiet concentration. Natural window light from the
side. A mug and an opened envelope on the table. Not looking at the camera. No
distress acting, no tears, no head in hands. Muted warm colour, 35mm grain,
shallow depth of field. Subject positioned in the lower two thirds of the frame.
Nothing on the paper is legible. 4:5 portrait.
```

---

## 8. Who uses it — been here before

**Type:** Image
**Aspect ratio:** 4:3 — 1200 × 900
**Save as:** `frontend/public/media/persona-2.jpg`

```
Documentary photograph of a person in their thirties at a desk with an open
laptop and a neat ring binder of prior correspondence beside them, mid-task.
Competent and unhurried — not weary, not triumphant. Daylight from a window. Not
looking at the camera. Muted warm palette, natural film grain, shallow depth of
field. Screen content not legible. No medical props of any kind. 4:3 landscape.
```

---

## 9. Who uses it — for someone else

**Type:** Image
**Aspect ratio:** 1:1 — 1100 × 1100
**Save as:** `frontend/public/media/persona-3.jpg`

```
Documentary photograph of a person in their fifties sitting in a waiting-room
chair, holding a phone in both hands and reading it, a tote bag and a folder on
the seat beside them. They are handling something for somebody else. Neutral
institutional interior, soft diffuse light, deliberately unremarkable. Phone
screen not legible. Not looking at the camera. No distress acting, no hospital
signage, no medical equipment visible. Muted warm colour, natural grain.
1:1 square.
```

---

## 10. Empty state — no cases yet

**Type:** Illustration (SVG preferred; PNG with transparency is fine)
**Aspect ratio:** 4:3 — 640 × 480
**Save as:** `frontend/public/media/empty-cases.svg`

> Most users' first view of the app, so it has to read as an invitation rather
> than a shrug.

```
A minimal two-tone line illustration of a single closed cardboard document
folder lying flat on a plain surface, seen at a slight three-quarter angle.
Uniform 1.5px line weight in warm grey (#DED5C6), with one subtle flat fill in
pale cream. Exactly two tones — no shading, no gradient, no texture. No faces,
no characters, no mascot, no hands, no arrows. Calm and geometric, with generous
empty space around the object. Flat vector style on a white background.
4:3 landscape.
```

---

## 11. Upload drop zone

**Type:** Illustration (SVG preferred; PNG with transparency is fine)
**Aspect ratio:** 1:1 — 512 × 512
**Save as:** `frontend/public/media/upload-icon.svg`

> Must use the **same line vocabulary** as #10 — they appear in the same app.

```
A minimal two-tone line illustration of a single sheet of paper being placed
into an open document folder, seen at a slight angle. Uniform 1.5px line weight
in warm grey (#DED5C6) with one pale cream flat fill. Exactly two tones, no
shading, no gradients. No hands, no arrows, no cloud symbol, no mascot. Flat
vector style, generous empty space, white background. 1:1 square.
```

---

## 12. How to photograph a letter

**Type:** Image
**Aspect ratio:** 3:4 — 900 × 1200
**Save as:** `frontend/public/media/camera-guide.jpg`

> This one genuinely teaches something, so clarity beats beauty.

```
A phone held in portrait orientation photographing a single sheet of printed
paper lying flat on a wooden table, seen over the photographer's shoulder. The
phone screen shows the page filling the frame with all four corners visible and
thin white corner guide brackets overlaid. Good even daylight with no shadow
falling across the page. The phone is held square to the paper and parallel to
it. The paper's text is visible as grey typographic texture but not readable.
Instructional and clear rather than artful. Warm neutral palette.
3:4 portrait.
```

---

## 13. Social share card

**Type:** Image
**Aspect ratio:** 1.91:1 — 1200 × 630
**Save as:** `frontend/public/media/og-card.png`

> **This one contains text, and the wording must be exact:**
> - `APPEAL ARCHITECT` — small, monospace, letter-spaced, upper case
> - `Your denial, formally refuted.` — large, the dominant element
>
> If your generator renders lettering badly, make the background with the prompt
> and set the type in any design tool. Wrong-looking text on a share card is
> worse than no card at all.

```
A minimal social share card on a warm cream background (#F2EDE4). In the lower
right, the edge of a single document card in off-white (#FFFCF7) with a thin
warm grey border and a soft shadow, entering the frame at a slight angle and
cropped by the edge. Generous empty space across the upper left two thirds,
left clear for text. No faces, no numbers, no statistics, no logo marks, no
icons. Flat, quiet and editorial. Warm cream, off-white, charcoal, and one small
deep forest green element. 1200 x 630.
```

---

## After you generate them

```bash
# From the repo root — check your filenames match
ls -1 frontend/public/media/

# Confirm nothing shifted
cd frontend && npm run build
```

Ship 2× raster where your tool offers it. Every slot keeps its exact aspect
ratio either way, so a wrong-sized file will be letterboxed rather than breaking
the layout — but matching the sizes above avoids any upscaling.

---

## Two slots the design listed that the build does not use

Recorded so you do not generate them by mistake:

- **`trust-strip`** (security and privacy marks, 8:1) — the landing page states
  the privacy position in words and links to `/legal` instead. A strip of
  security badges reads as reassurance theatre, which is the opposite of what
  this design is doing.
- **`graph-legend`** (first-run overlay, 3:2) — the argument graph has a legend
  section on the page itself, which cannot be dismissed and lost.

If you want either, say so and the slot goes back in.
