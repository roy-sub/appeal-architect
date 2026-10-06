export const heroFacts = [
  { k: "Fixed promise", v: "Every paragraph backed by a rule" },
  { k: "Free to start", v: "Four questions, no account" },
  { k: "Rules current", v: "5 Oct 2026 · version 2026.10.1" },
];

export const marquee = [
  "Every paragraph backed by a rule",
  "Deadlines counted from your own letter",
  "Arguments the insurer cannot knock back",
  "Encrypted. Never shared with your insurer.",
  "No outcome is ever promised",
];

export const stats = [
  { n: "0.2", suf: "%", label: "of denied claims are ever appealed", note: "Fewer than two people in a thousand push back." },
  { n: "50", suf: "%", label: "of filed appeals are overturned", note: "Across internal review and independent external review." },
  { n: "180", suf: " days", label: "is a common internal-appeal window", note: "Yours depends on your plan type. We work out which one you are on." },
];

export const steps = [
  { num: "01", title: "Upload the letter", body: "Photograph it with your phone or drop the PDF. We read the reason code, the claim number, the dates and the policy sections it cites." },
  { num: "02", title: "Confirm what we read", body: "Every fact sits beside the exact sentence it came from. You confirm, edit or reject each one. Nothing moves on until the required facts are confirmed." },
  { num: "03", title: "See the route and the argument", body: "Your appeal track, your deadlines with the rule behind each, the arguments that hold against their stated reason, and the letter that uses only those." },
];

export const capabilities = [
  {
    source: "Your plan document, § 11.2",
    quote: "You have the right to request an internal appeal within the timeframe specified in your plan documents.",
    title: "Your deadlines, and the rule each one came from",
    body: "We read your plan type from the letter, then work out every date: when the internal appeal is due, how long they have to answer, and when the external review window opens and closes. Open any date to see the trigger date it was counted from and the regulation that sets the count.",
    cite: "29 C.F.R. § 2560.503-1(h)(3)(i) · counted from 14 Sep 2026",
    slot: "feature-roadmap", ratio: "16 / 10", kind: "image" as const,
    slotLabel: "The procedural roadmap with deadlines", intrinsic: "1600×1000",
  },
  {
    source: "Your denial letter, page 1",
    quote: "The requested service is not medically necessary as defined in the plan.",
    title: "Solid ground, and worth adding",
    body: "We treat that sentence as an argument and build the counter-arguments that attack it. Then we check each one against what the insurer would most likely say back. Three survive whatever they answer. Two only help under a narrow reading, so they are labelled that way instead of being passed off as strong.",
    cite: "Reason code CO-50 · 3 solid ground · 2 worth adding · 1 left out",
    slot: "feature-graph", ratio: "16 / 10", kind: "image" as const,
    slotLabel: "The argument graph, solid ground against worth adding", intrinsic: "1600×1000",
  },
  {
    source: "Your denial letter, page 2",
    quote: "Plan provision 7.4(b) excludes services that are investigational.",
    title: "Every paragraph backed by a rule",
    body: "The letter is assembled only from arguments that hold. Each paragraph carries the node it came from, so you can click a sentence and see exactly why it is in there. You edit it, you sign it, you send it. We tell you where to send it and how to prove it arrived on time.",
    cite: "Exports to PDF and DOCX · prints on US Letter with correct margins",
    slot: "feature-letter", ratio: "4 / 5", kind: "image" as const,
    slotLabel: "A generated appeal letter page with citation markers", intrinsic: "1200×1500",
  },
  {
    source: "Your denial letter, page 3",
    quote: "You may submit any additional documentation you wish the reviewer to consider.",
    title: "The evidence list writes itself",
    body: "That sentence is where most appeals quietly fail. We turn it into a specific list: which records, from whom, covering which dates, and the exact points your doctor’s letter has to make for this case. Each item says which argument needs it, so nothing on the list is there for padding.",
    cite: "8 items · 6 on file · 1 requested · 1 optional",
    slot: "feature-evidence", ratio: "16 / 10", kind: "video" as const,
    slotLabel: "Evidence checklist items being satisfied", intrinsic: "1600×1000",
  },
];

export const personas = [
  { slot: "persona-1", ratio: "4 / 5", intrinsic: "1000×1250", alt: "A person at a kitchen table with a letter, mid-afternoon", tag: "First time", title: "You just got the letter", body: "Three days ago. You have read it four times. You do not know whether this is normal or how long you have. Start with the free check." },
  { slot: "persona-2", ratio: "4 / 3", intrinsic: "1200×900", alt: "A person managing a chronic condition at a laptop, prior correspondence beside them", tag: "Been here before", title: "This is the fourth one this year", body: "You know the process. You want the workspace, the dates, and the letter, without being explained things you already know." },
  { slot: "persona-3", ratio: "1 / 1", intrinsic: "1100×1100", alt: "A caregiver on a phone in a waiting room, handling it for someone else", tag: "For someone else", title: "You are handling it for someone else", body: "For a parent or a child, on a phone, between other things. The case holds its state and the reminders find you." },
];

export const plans = [
  {
    name: "Free check", price: "$0", unit: "", featured: false, href: "/triage/",
    blurb: "Four questions. Find out which track you are on and roughly when your door closes.",
    items: ["Likely appeal track", "Estimated deadline with the rule", "An honest read on whether to appeal", "No account needed"],
    cta: "Start the free check",
  },
  {
    name: "Appeal Package", price: "$149", unit: "once, per case", featured: true, href: "/cases/",
    blurb: "Everything needed to prepare and file one appeal, through external review if it gets there.",
    items: ["Document extraction you confirm line by line", "Roadmap with every deadline cited", "Argument graph: solid ground and worth adding", "Evidence checklist and physician-letter template", "Letter editor, PDF and DOCX export", "Reminders at 30, 14, 7, 3 and 1 days"],
    cta: "Open a case",
  },
  {
    name: "Ongoing", price: "$19", unit: "per month", featured: false, href: "/cases/",
    blurb: "For people denied more than once a year, and for caregivers running several at a time.",
    items: ["Unlimited cases", "Plan documents saved and reused", "Family members and dependants", "Reminder emails for every open deadline"],
    cta: "Choose ongoing",
  },
];

export const faqs = [
  { q: "Is this legal advice?", a: "No. Appeal Architect prepares documents and explains procedure. It is not legal or medical advice, and it does not represent you. You review and file everything yourself. If your case needs a lawyer, we will say so rather than pretend otherwise." },
  { q: "What happens to my documents?", a: "They are encrypted and stored against your case so you can come back to them. They are not sold, not used to train anything, and not shared with your insurer. You can delete a case, or your whole account, from Settings, and the files go with it." },
  { q: "Does this work for Medicare or Medicaid?", a: "Partly. Medicare Advantage and Medicaid managed care follow different rules, with shorter deadlines and different review bodies. The free check tells you which track you are on. If we cannot route your case accurately we will tell you instead of guessing." },
  { q: "What if my deadline has already passed?", a: "Sometimes there is still a route — a late filing with good cause, a second claim, or an external review window that runs on a different clock. Run the free check and it will say plainly whether a door is still open." },
  { q: "What if I buy the package and change my mind?", a: "Full refund within 14 days as long as you have not exported a letter. If the rules engine cannot determine your track, you are refunded automatically and we tell you why." },
];
