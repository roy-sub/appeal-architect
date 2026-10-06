# Appeal Architect — Design Brief 

## 1. What the product actually is

Your health insurer refused to pay. You got a letter. It cites a policy section you have never read and a reason code that means nothing to you. Almost nobody fights this — under 0.2% of people appeal — and yet roughly half of the people who do appeal win.

The reason people don't fight is not that they don't care. It is that the process is genuinely unmappable: which rules apply depends on what kind of insurance you have, and each kind has different deadlines, different review bodies, different forms, and different rights. Miss a deadline and the door closes permanently.

Appeal Architect does two things:

**One — the route.** From the denial letter and a few questions, a rules engine works out which appeal track you are legally on, what the review levels are, exactly what your deadlines are, and what each step requires. Every conclusion shows the rule it came from.

**Two — the argument.** The insurer's stated reason for denying is treated as an argument. The engine builds the counter-arguments that attack it — from your policy's own coverage terms, medical-necessity criteria, state mandates, the insurer's own clinical guidelines, your doctor's letter — and computes which of them survive the insurer's likely responses. The ones that survive unconditionally are your solid ground. The ones that survive only under some readings are worth adding. Then it writes the appeal letter using only the arguments that hold, with every paragraph traceable to a node in that graph.

## 2. Who is looking at this

- **The blindsided patient.** Got the letter three days ago. Has read it four times. Does not know whether this is normal, whether it is worth fighting, or how long they have. First-time user, will decide within 30 seconds whether this app is a scam.
- **The chronic-condition manager.** Fourth denial this year on a specialty drug. Knows the process better than most. Wants speed, a workspace, and not to be explained things they already know.
- **The caregiver.** Handling this for a parent with dementia or a child. Managing three things at once, on a phone, tired. Needs the app to hold state and remind them.
- **Later: professional patient advocates.** Multi-case dashboards.

Every one of them is under stress and none of them want a product that performs cheerfulness at them.

## 3. Positioning and voice

**Positioning:** a self-help document-preparation and information tool. Not legal advice, not medical advice, not representation. The user reviews and files everything themselves. This is a legal constraint as much as a brand one, and it should read as honesty rather than as hedging.

**Voice:** a very good advocate who has done this a thousand times and is not alarmed. Plain, specific, steady. Explains without condescending. Says what is true including when it is not encouraging.

Fixed strings — use verbatim:
- Product name: **Appeal Architect**
- Primary promise: **Your denial, formally refuted.**
- Method promise: **Every paragraph backed by a rule.**
- Disclaimer, in the footer and in every generated letter: *Appeal Architect prepares documents and explains procedure. It is not legal or medical advice, and it does not represent you. You review and file everything yourself.*
- Rules stamp on every route determination: *Rules current as of {date} · version {v}*
- The two argument tiers: **Solid ground** and **Worth adding**. These exact labels.

Never say: guaranteed, we'll win, fight back (as a headline verb), don't let them get away with it, hack, loophole, secret. No war metaphors. Nobody in this situation wants to be told they are in a battle.

## 4. Visual direction

The subject matter is **the dossier** — the letter, the policy document, the evidence, the record of what was said and when. Not "healthtech" (blue gradients, abstract wellness) and not "legaltech" (columns, gavels, navy-and-gold authority theatre).

**Direction to pursue:** a light-first reading environment built for documents. Real paper logic — margins, rules, marginalia, citation, annotation. Warm neutral ground, ink you can read for twenty minutes, and colour reserved almost entirely for two jobs: **time** (deadlines) and **standing** (whether an argument holds). When colour appears, it means one of those two things.

The single most distinctive opportunity: **annotation**. This product's real gesture is taking an insurer's sentence and writing in the margin next to it *this is refuted, and here is why.* Let that gesture be the visual identity — quoted source text on one side, the argument that attacks it alongside, connected.

**What to avoid, because it is where this brief would drift by default:**
- Cream (#F4F1EA) plus a high-contrast serif display plus a terracotta accent. That combination is currently everywhere; it is not a choice.
- Hospital blue, wellness mint, insurance-brochure stock photography of a smiling family.
- Gavels, scales of justice, shields, checkmark-in-a-circle heroes.
- Identical rounded cards in a 3-column grid for everything.
- ALL-CAPS tracked-out eyebrow labels above each section.
- Red-alert deadline treatments. Urgency is communicated by proximity, position and precision, not by shouting.

**Colour, as direction not prescription:** you need a warm neutral ground and a deep readable ink; one colour for time that can express a gradient from "plenty" to "act now" without ever reading as an emergency alarm; and a small standing palette that distinguishes *insurer's claim* / *solid ground* / *worth adding* / *defeated*. That standing palette must survive greyscale and colour-blindness — pair it with weight, border style or shape.

**Typography:** one or two Google Fonts. This app is read, not scanned: long appeal letters, quoted policy language, procedural explanation. Prioritise a body face that is comfortable at 17–19px on a phone with generous leading, has real italics for quoted policy text, and has tabular numerals for dates and dollar figures.

**Motion:** one orchestrated moment per screen.
- The **argument graph resolving** — the insurer's argument sits alone, counter-arguments arrive and attach, defeated ones recede — is the showiest moment in the product, and it is doing explanatory work, so it is earned. It must also be skippable and must degrade to a static, equally legible diagram.
- The **letter assembling** from confirmed argument nodes is the second.
- Everywhere else motion answers an action: a fact confirmed, a checklist item satisfied, a deadline acknowledged.
- Never animate a countdown continuously. A number ticking down in someone's peripheral vision while they read is cruel.
- `prefers-reduced-motion` collapses everything to instant state changes with no information lost.

## 5. Media plan

I will add real media later. Design the slots and their placeholder states.

| id | Page | Type | Ratio | What it will show |
|---|---|---|---|---|
| `hero-loop` | Landing | video (muted, loop) | 16:9 | A denial letter being uploaded, facts appearing as confirmable chips, a roadmap resolving |
| `hero-poster` | Landing | image | 16:9 | Poster frame / reduced-motion fallback |
| `feature-roadmap` | Landing | image | 4:3 | The procedural roadmap with deadlines |
| `feature-graph` | Landing | image | 4:3 | The argument graph, solid ground vs worth adding |
| `feature-letter` | Landing | image | 3:4 | A generated appeal letter page with citation markers |
| `feature-evidence` | Landing | video | 1:1 | Evidence checklist items being satisfied |
| `stat-backdrop` | Landing | image | 21:9 | Quiet backdrop for the denial/appeal statistics band |
| `persona-{1,2,3}` | Landing | image | 1:1 | Patient / chronic manager / caregiver portraits |
| `trust-strip` | Landing | image strip | — | Security and privacy marks |
| `og-default` | Meta | image | 1200×630 | Social card |
| `empty-cases` | App | illustration | 1:1 | Empty state, case list |
| `empty-evidence` | App | illustration | 1:1 | Empty state, evidence checklist |
| `scan-guide` | App | image | 3:4 | How to photograph a denial letter well |

Placeholders must reserve the exact aspect ratio (no layout shift), fill with a designed state consistent with the system, and show the slot id in dev mode only.

## 6. Screens to produce

### Marketing site (public)
1. **Landing.** Hero, the statistics band (denial rates vs appeal rates vs overturn rates — this is the argument for using the product and should be the emotional turn of the page), how it works in three real steps, the four capability sections keyed to the media slots, pricing, FAQ, footer with the full disclaimer.
2. **Free triage tool.** Three or four questions → "here is the track you are probably on, here is your likely deadline, here is whether this is worth appealing." No account. This is the funnel and the goodwill.
3. **Pricing.** Free triage / one-time Appeal Package / subscription / (later) advocate Pro.
4. **Legal.** Terms, privacy in plain language, the disclaimer in full, the rules changelog.

### Product (authenticated)
5. **Sign in / sign up.** Email and magic link. Say what happens to their documents, right there on this screen.
6. **Case list.** Each case: insurer, claim, denial reason, current stage, next deadline with days remaining, status. The empty state is most users' first view — make it an invitation to upload, not a shrug.
7. **Upload wizard.** Denial letter (PDF or phone photo), optionally EOB, plan documents, medical records. Camera capture path on mobile with the `scan-guide` media. Clear progress; clear statement of what happens to the file.
8. **Extraction review.** The heart of the trust model. Split view: the document on one side, extracted facts on the other, each fact linked to the exact span it came from, each with a confidence indication and confirm / edit / reject. Nothing proceeds until the required facts are confirmed. Design the *editing* case well — extraction will be wrong sometimes and that must feel normal, not like a failure.
9. **Procedural roadmap.** A timeline: internal appeal → insurer response window → external review → decision. Per step: deadline date, days remaining, who files, what is required, and the citation for that rule. A deadline detail drawer explains how the date was calculated, from which trigger date, under which rule.
10. **Argument graph.** Insurer's argument(s) at the top. Counter-arguments attached beneath, split into **Solid ground** and **Worth adding**. Per argument: what it asserts, what evidence it needs, current evidence status, what the insurer would likely say back and whether that response defeats it. Needs a genuine mobile treatment — consider a stacked/list form on small screens rather than a shrunken graph.
11. **Evidence checklist.** Derived from the accepted arguments. Per item: what it is, why it is needed (link to the argument node that needs it), how to get it, status, upload. Includes a physician-letter template with the specific points that letter must make for this case.
12. **Letter editor.** Generated appeal letter. Each paragraph shows which argument node it came from; clicking a paragraph highlights that node. Editable, versioned, exportable to PDF and DOCX, with a print/mail checklist (who to send to, what to include, how to prove it was sent on time).
13. **Case timeline.** Log of everything: uploaded, confirmed, generated, sent, responded. This is the record the user may need later.
14. **Escalation.** If the internal appeal is denied, the next-level flow — external review request, with its own deadline, form and requirements.
15. **Settings.** Profile, family members/dependants managed, notification preferences, billing, **delete my data** (prominent, honest, and actually working).

### System
16. Loading, empty, error, offline for every data surface. Extraction takes time — design the waiting state with visible stages ("reading the letter", "finding the reason codes", "matching your plan type"), not a spinner.
17. Toasts, modals, confirmation dialogs. The destructive-action dialog matters here.
18. Email templates: magic link, deadline reminder at 30/14/7/3/1 days, extraction complete, letter ready. Design these too — the reminder email is a core feature.
19. 404 and 500.

## 7. Component inventory to define

`DeadlineCard` + `DeadlineRing` (urgency by proximity, never alarm) · `RoadmapTimeline` + `RoadmapStep` · `ArgumentNode` (insurer / solid-ground / worth-adding / defeated) · `ArgumentGraph` (desktop) + `ArgumentList` (mobile) · `AttackConnector` · `EvidenceRow` + `EvidenceChecklist` · `FactChip` (pending / confirmed / edited / rejected) · `SourceSpanHighlight` · `DocumentViewer` · `CitationChip` · `LetterParagraph` (with node backlink) · `StatusPill` · `RulesStamp` · `DisclaimerBanner` · `UploadDropzone` + `CameraCapture` · `ExtractionProgress` · `CaseCard` · `EmptyState` · `MediaSlot` · `DestructiveDialog`.

For each: variants, all interaction states, props.

## 8. Technical constraints the design must respect

- Implementation is **Next.js 15 App Router, static export**, Tailwind CSS v4, shadcn/ui, Framer Motion, React Flow for the argument graph, `react-pdf` / PDF.js for the document viewer.
- Static export means no SSR, no server actions, no Next.js image optimisation. Specify exact intrinsic asset sizes; keep the hero video small.
- Tokens as CSS custom properties **and** a `tailwind.config.ts` theme extension that agree exactly.
- Light is primary, dark is derived; both complete; theme via `data-theme` on `<html>`.
- **Mobile is a first-class target**, not a reduction. Assume phone camera upload, one-handed use, poor connection, and a user who will do the whole flow on that phone.
- Print styles matter: the letter must print cleanly on US Letter with correct margins.
- Target: LCP under 2.5s on landing with media; app shell interactive under 1s.

## 9. What success looks like

Someone opens the denial letter they have been avoiding, uploads it, and within two minutes sees: *you have 163 days, here is the rule that says so, here are the three arguments that hold against their reason, and here is what your doctor needs to write.* They stop feeling helpless. Everything in the design serves that.
