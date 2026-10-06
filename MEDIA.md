# Media to generate

Thirteen assets. Every one has a reserved slot in the code already, holding its
exact aspect ratio — so dropping a file in changes **no layout**. Until a file
exists the slot renders its designed placeholder, which is intentional and
shippable.

## How to use this document

1. Generate the image with the prompt given.
2. Save it at **exactly** the path under "Save as". The filename is what the
   code looks for.
3. Reload. Nothing else to do — no manifest to edit, no import to add.

All paths are relative to the repo root. Create `frontend/public/media/` if it
does not exist (it does, with a README in it).

```bash
# After generating, from the repo root:
ls frontend/public/media/          # check your filenames match
cd frontend && npm run build       # confirm nothing shifted
```

## House rules for every asset

These are not stylistic preferences — they are what keeps the product credible
to someone who is frightened and deciding within thirty seconds whether this is
a scam.

- **Nothing may depict a win.** No celebration, no cheque, no thumbs-up, no
  handshake, no raised fist, no confetti. The product never implies an outcome.
- **No legal or medical iconography.** No gavels, no scales of justice, no
  shields, no stethoscopes, no clipboards, no white coats.
- **No stock-photo emotion.** Nobody acting distressed, nobody beaming. Unposed,
  no eye contact with camera.
- **Documentary, warm, quiet.** Think a reportage photographer in somebody's
  kitchen in late afternoon, not a brochure.
- **The palette is warm paper and deep forest green**, with a single clay-orange
  accent. Avoid blue entirely — blue reads "hospital portal", which is the thing
  this design deliberately is not. Hex values if your tool takes them:
  ground `#F2EDE4`, surface `#FFFCF7`, ink `#1C1A17`, forest `#14453A`,
  clay `#C85A33`.
- **No text in any image** unless the entry says otherwise. Generated lettering
  is always slightly wrong and it is the first thing that reads as fake.
- **Real paper, real desks, real light.** The subject matter is the dossier.

---

## 1. Hero background

- **Save as:** `frontend/public/media/hero-bg.mp4` (and a still fallback as
  `frontend/public/media/hero-bg.jpg`)
- **Where it appears:** the landing page hero, full-bleed behind the headline
- **Size:** 2560 × 1440. Video ≤ 16 seconds, muted, loops, ≤ 4 MB
- **Critical:** this sits under a heavy forest-green scrim at 34–93% opacity with
  white text over it. It must be **low contrast with no legible detail and no
  fast motion**. A still image at the same size is an acceptable substitute and
  honestly may look better.

> **Prompt.** Slow documentary footage, late afternoon in a modest home kitchen.
> Over-the-shoulder framing, shallow depth of field. A person in their fifties
> sits at a wooden table holding a single sheet of printed paper, reading it. A
> mug, a pair of reading glasses, an opened envelope on the table. Warm low sun
> through a window to one side, dust in the light. Muted warm palette — oatmeal,
> faded terracotta, worn wood. Almost no camera movement; a very slow push in.
> Nothing on the paper is legible. The person is calm and absorbed, not
> distressed. Grainy 35mm feel, soft shadows, no colour grading towards blue.
> Nobody looks at the camera.

---

## 2. Statistics band backdrop

- **Save as:** `frontend/public/media/stat-backdrop.jpg`
- **Where it appears:** behind the big numbers on the landing page
- **Size:** 2100 × 900
- **Critical:** renders at **14% opacity** behind large numerals. It must read as
  texture, never as a photograph competing with the figures.

> **Prompt.** Near-abstract macro photograph of the stacked edges of a thick pile
> of paper documents, shot almost edge-on in raking low light so each sheet edge
> catches a thin highlight. Warm cream and pale ochre tones. Very shallow depth
> of field, most of the frame falling soft. No text, no hands, no visible page
> content. Quiet, archival, like a records room. High key, low contrast.

---

## 3. Feature — the roadmap

- **Save as:** `frontend/public/media/feature-roadmap.png`
- **Where it appears:** landing page, first capability section
- **Size:** 1600 × 1000 (16:10)

> **Prompt.** A clean product screenshot mockup of a web application, light
> theme, on a warm off-white background (#FFFCF7). It shows a horizontal
> procedural timeline of four numbered steps, each a card with a soft rounded
> corner. Each card has a small circular progress ring in deep forest green
> (#14453A), a bold date, and two short lines of grey text beneath. A thin
> hairline rule runs behind the row connecting the steps. Typography is a clean
> humanist sans serif. Generous whitespace, Swiss-grid alignment. Palette strictly
> warm cream, deep green and charcoal with one small orange accent button. No
> browser chrome, no cursor, no photographic elements. Crisp, flat, no gradients
> or glass effects.

---

## 4. Feature — the argument graph

- **Save as:** `frontend/public/media/feature-graph.png`
- **Where it appears:** landing page, second capability section
- **Size:** 1600 × 1000 (16:10)
- **This is the product's centrepiece.** Worth generating several times.

> **Prompt.** A clean product screenshot mockup of a web application, light theme
> on warm off-white. At the top centre, a single card with a sharp 2px corner
> radius and a 1.5px solid charcoal border, representing a claim. Thin hairline
> connector lines descend from it to two columns of cards below. The left column's
> cards have a **solid** deep-forest-green border with a thicker 3px green bar
> down the left edge and a small filled circle marker. The right column's cards
> have a **dashed** grey border and a small diamond outline marker. Each card
> contains a short bold line and two lines of smaller grey text. Clean humanist
> sans serif, lots of whitespace, strict alignment. Warm cream, deep green,
> charcoal. No browser chrome, no photographs, no glow or 3D.

---

## 5. Feature — the letter

- **Save as:** `frontend/public/media/feature-letter.png`
- **Where it appears:** landing page, third capability section
- **Size:** 1200 × 1500 (4:5)

> **Prompt.** A single page of a formal business letter on warm white paper,
> photographed flat from directly above in soft even light. Dense justified
> body text set in a readable book serif — legible as typography but the words
> themselves blurred or indistinct. Generous one-inch margins. In the left
> margin beside each paragraph sits a small monospace reference tag in muted
> grey. A signature line and date block at the foot. The page sits on a warm
> cream surface with a barely visible shadow at its edge. No letterhead logo, no
> readable names, no addresses. Calm, precise, archival.

---

## 6. Feature — evidence being satisfied

- **Save as:** `frontend/public/media/feature-evidence.mp4`
- **Where it appears:** landing page, fourth capability section
- **Size:** 1600 × 1000 (16:10). ≤ 8 seconds, muted, loops, ≤ 2 MB

> **Prompt.** A short screen-recording style animation, light theme on warm
> off-white. A vertical checklist of five rows, each with a small square
> checkbox on the left, a bold label, and a line of smaller grey text. One at a
> time, from the top, each checkbox fills with deep forest green and its row
> settles very slightly in opacity. Beneath each satisfied row a small monospace
> reference appears. Movement is calm and slow, one row roughly every 1.2
> seconds. No cursor, no clicking sound, no confetti, no tick-burst. Clean
> humanist sans serif, generous spacing.

---

## 7, 8, 9. The three people who use it

Three portraits. All documentary, all unposed, **none** of them performing
distress or relief. **Note the different ratios** — the slots do not match.

### 7. First-time patient

- **Save as:** `frontend/public/media/persona-1.jpg`
- **Size:** 1000 × 1250 (**4:5, portrait**)

> **Prompt.** Documentary photograph, mid-afternoon, a person in their forties
> sitting at a kitchen table in a modest home, a single sheet of printed paper in
> one hand, looking at it with quiet concentration. Natural window light from the
> side. A mug and an opened envelope on the table. Not looking at the camera. No
> distress acting, no tears, no head in hands. Muted warm colour, 35mm grain,
> shallow depth of field. Subject positioned in the lower two thirds of the frame.
> Nothing on the paper is legible.

### 8. Chronic-condition manager

- **Save as:** `frontend/public/media/persona-2.jpg`
- **Size:** 1200 × 900 (**4:3, landscape**)

> **Prompt.** Documentary photograph of a person in their thirties at a desk with
> an open laptop, a neat ring binder of prior correspondence beside them, mid
> task. Competent and unhurried — not weary, not triumphant. Daylight from a
> window. Not looking at the camera. Muted warm palette, natural grain, shallow
> depth of field. Screen content not legible. No medical props.

### 9. Caregiver

- **Save as:** `frontend/public/media/persona-3.jpg`
- **Size:** 1100 × 1100 (**1:1, square**)

> **Prompt.** Documentary photograph of a person in their fifties sitting in a
> waiting-room chair, holding a phone in both hands and reading it, a tote bag
> and a folder on the seat beside them. Handling something for somebody else.
> Neutral institutional interior, soft diffuse light, deliberately unremarkable.
> Phone screen not legible. Not looking at the camera. No distress acting, no
> hospital signage, no medical equipment visible. Muted warm colour, natural
> grain.

---

## 10. Empty state — no cases yet

- **Save as:** `frontend/public/media/empty-cases.svg`
- **Where it appears:** the case list, before the first case. **This is most
  users' first view of the app**, so it has to read as an invitation.
- **Size:** 640 × 480 (4:3)

> **Prompt.** A minimal two-tone line illustration, SVG style, of a single closed
> cardboard document folder lying flat on a plain surface, seen at a slight
> three-quarter angle. Uniform 1.5px line weight in warm grey (#DED5C6), with one
> subtle flat fill in pale cream. Exactly two tones, no shading, no gradient, no
> texture. No faces, no characters, no mascot, no hands, no arrows. Calm,
> geometric, lots of empty space around the object. Flat vector, white background.

---

## 11. Upload drop zone

- **Save as:** `frontend/public/media/upload-icon.svg`
- **Where it appears:** the upload screen
- **Size:** 512 × 512 (1:1)
- Must use the **same line vocabulary** as #10 — they appear in the same app.

> **Prompt.** A minimal two-tone line illustration, SVG style, of a single sheet
> of paper being placed into an open document folder, seen from a slight angle.
> Uniform 1.5px line weight in warm grey (#DED5C6) with one pale cream flat fill.
> Exactly two tones, no shading or gradients. No hands, no arrows, no cloud
> symbol, no mascot. Flat vector, generous empty space, white background.

---

## 12. How to photograph a letter

- **Save as:** `frontend/public/media/camera-guide.jpg`
- **Where it appears:** beside the upload drop zone, as guidance. This one
  genuinely teaches something, so clarity beats beauty.
- **Size:** 900 × 1200 (3:4)

> **Prompt.** A phone held in portrait orientation photographing a single sheet
> of printed paper lying flat on a wooden table, seen over the photographer's
> shoulder. The phone screen shows the page filling the frame with all four
> corners visible and thin white corner guide brackets overlaid. Good even
> daylight, no shadow falling across the page, phone held square to the paper and
> parallel. The paper's text is visible as grey typographic texture but not
> readable. Instructional and clear rather than artful. Warm neutral palette.

---

## 13. Social share card

- **Save as:** `frontend/public/media/og-card.png`
- **Where it appears:** link previews on social and in messages
- **Size:** 1200 × 630
- **This one does contain text**, and the text must be exact:
  - `APPEAL ARCHITECT` — small, monospace, letter-spaced, upper case
  - `Your denial, formally refuted.` — large, the dominant element
- If your generator renders lettering badly, make the background in the
  generator and set the type in any design tool. Wrong-looking text on a share
  card is worse than no card.

> **Prompt.** A minimal social share card, 1200 × 630, on a warm cream
> background (#F2EDE4). Lower right: the edge of a single document card in off
> white (#FFFCF7) with a thin warm grey border and a soft shadow, entering the
> frame at a slight angle and cropped by the edge. Generous empty space in the
> upper left two thirds for text. No faces, no numbers, no statistics, no logo
> marks, no icons. Flat, quiet, editorial. Warm cream, off white, charcoal and
> one small deep forest green element.

---

## Two slots the design listed that the build does not use

Recorded so you do not generate them by mistake:

- **`trust-strip`** (security and privacy marks, 8:1) — the landing page states
  the privacy position in words and links to `/legal` instead. A strip of
  security badges reads as reassurance theatre, which is the opposite of what
  this design is doing.
- **`graph-legend`** (first-run overlay, 3:2) — the argument graph has a built-in
  legend section on the page, which does not need to be dismissed and cannot be
  lost.

If you want either, say so and I will add the slot back.

## Checklist

```
frontend/public/media/
├── hero-bg.mp4            1  2560×1440  video, ≤16s, low contrast
├── hero-bg.jpg            1  2560×1440  still fallback
├── stat-backdrop.jpg      2  2100×900   renders at 14% opacity
├── feature-roadmap.png    3  1600×1000
├── feature-graph.png      4  1600×1000  the centrepiece
├── feature-letter.png     5  1200×1500
├── feature-evidence.mp4   6  1600×1000  video, ≤8s
├── persona-1.jpg          7  1000×1250  4:5 portrait
├── persona-2.jpg          8  1200×900   4:3 landscape
├── persona-3.jpg          9  1100×1100  1:1 square
├── empty-cases.svg       10  640×480    two-tone line art
├── upload-icon.svg       11  512×512    same line vocabulary as #10
├── camera-guide.jpg      12  900×1200
└── og-card.png           13  1200×630   contains exact text
```

Ship 2× raster where your tool offers it. Nothing here blocks launch — every
slot has a designed placeholder and the layout is already correct without them.
