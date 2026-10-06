import Link from "next/link";

import { DISCLAIMER } from "@/lib/site";

export const metadata = {
  title: "Legal — Appeal Architect",
  description:
    "Terms, privacy in plain language, the full disclaimer, and the rules changelog.",
};

const label = "font-mono text-[11px] tracking-[.06em] text-ink-muted";
const h2 =
  "mt-12 mb-3 text-[23px] leading-[30px] font-semibold tracking-[-0.01em] text-ink";
const h3 = "mt-7 mb-2 text-[18px] leading-[25px] font-semibold text-ink";
const p = "mt-0 mb-4 text-pretty text-[17px] leading-[28px] text-ink";

export default function LegalPage() {
  return (
    <div className="min-h-dvh bg-ground">
      <header className="border-b border-rule">
        <div className="mx-auto flex h-[60px] items-center justify-between px-5 lg:h-[72px] lg:max-w-[1440px] lg:px-14">
          <Link
            href="/"
            className="font-mono text-[12px] font-medium uppercase tracking-[.14em] text-ink no-underline"
          >
            Appeal&nbsp;Architect
          </Link>
          <Link href="/triage/" className="text-[15px] text-clay-deep">
            Free check
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-[760px] px-5 py-12 lg:px-0 lg:py-[88px]">
        <div className={label}>LEGAL</div>
        <h1 className="mt-3.5 mb-0 text-[32px] leading-[40px] font-semibold tracking-[-0.02em] text-ink lg:text-[42px] lg:leading-[50px]">
          What this is, and what it is not
        </h1>

        {/* ---- the disclaimer, in full and first ---- */}
        <div className="mt-8 border-l-[3px] border-ink bg-surface px-5 py-5">
          <div className={label}>THE DISCLAIMER, IN FULL</div>
          <p className="mt-2.5 mb-0 text-pretty text-[17px] leading-[28px] font-medium text-ink">
            {DISCLAIMER}
          </p>
        </div>

        <h2 className={h2}>What we do</h2>
        <p className={p}>
          We work out which appeal track your plan puts you on, what your deadlines
          are, and what each step requires, and we show you the regulation behind every
          one of those conclusions. We then build the counter-arguments against the
          reason your insurer gave, compute which of them survive what the insurer is
          likely to say back, and write an appeal letter from the ones that hold.
        </p>
        <p className={p}>
          A rules engine does the legal reasoning, not an AI model. The model reads your
          documents and writes sentences. It never decides a deadline, a route, or
          whether an argument holds. That separation is enforced by the code and by a
          test that fails the build if it is violated.
        </p>

        <h2 className={h2}>What we are not</h2>
        <p className={p}>
          We are a document-preparation and information tool. We are not a law firm,
          not a medical provider, and not your representative. We do not file anything
          on your behalf, we do not speak to your insurer, and we do not appear for you
          at any level of review. You read everything we produce, you decide whether to
          use it, and you file it yourself.
        </p>
        <p className={p}>
          Nothing here is legal advice or medical advice. If your case turns on
          something unusual, or a deadline is close, a patient advocate or an attorney
          can do things we cannot.
        </p>

        <h3 className={h3}>About the dates we give you</h3>
        <p className={p}>
          Our deadlines are our reading of the regulations and of your plan. Where a
          regulation leaves the trigger date genuinely unclear, we take the earlier and
          more cautious reading and we tell you we have done so. We can still be wrong
          about your particular plan, which may give you longer than the federal
          minimum. Check every date against your own denial letter and your plan
          document before you rely on it.
        </p>
        <p className={p}>
          Some of the legal values in our rulebase have not yet been checked against
          their source by a person. Where that is true for your case, we say so on your
          roadmap. We would rather tell you that than let you assume otherwise.
        </p>

        <h2 className={h2}>Privacy, in plain language</h2>
        <p className={p}>
          Your denial letter names you, your insurer, your claim and your treatment,
          which means it names your diagnosis. We treat it accordingly.
        </p>
        <h3 className={h3}>What we hold</h3>
        <p className={p}>
          Your email address, the documents you upload, the text we read out of them,
          the facts you confirm, the route and arguments we compute, the letters we
          generate, and a log of what happened on your case and when. All of it is
          encrypted in transit and at rest.
        </p>
        <h3 className={h3}>Who can see it</h3>
        <p className={p}>
          You. Every record is tied to your account at the database level, not just in
          the application, so another account asking for your case gets nothing back.
          Documents live in a private store and are reached only through links that
          expire.
        </p>
        <h3 className={h3}>Where it goes outside our servers</h3>
        <p className={p}>
          One place: we send your document&rsquo;s text to Anthropic&rsquo;s API so a
          model can read it, and later we send the accepted arguments so a model can
          write the letter. That text is not used to train anything. We record that a
          call happened, which model, and how many tokens — never what was sent. We do
          not link those records to a case, because linking a call to a case is a step
          towards linking it to a diagnosis.
        </p>
        <h3 className={h3}>What never leaves</h3>
        <p className={p}>
          No clinical detail goes into an email. Your deadline reminders carry the
          deadline and the case title, because a reminder lands in an inbox that might
          be read on a shared screen. Nothing about your treatment is in a URL, where
          it would end up in server logs and browser history. There are no analytics or
          advertising trackers on any screen where your case is visible.
        </p>
        <h3 className={h3}>Deleting it</h3>
        <p className={p}>
          Delete my data deletes it. Rows and files, not a hidden flag. That includes
          your case history, which you may later wish you still had — we would rather
          say that here than surprise you. It cannot reach emails already delivered to
          you, or anything you exported and saved yourself.
        </p>
        <p className={p}>
          <Link href="/settings/" className="text-clay-deep">
            Delete my data
          </Link>
        </p>

        <h3 className={h3}>Who else is involved</h3>
        <p className={p}>
          The services this product needs to work: Supabase (database, sign-in,
          document storage), Anthropic (reading documents and writing prose), our email
          provider (sign-in links and deadline reminders), Stripe (payment), and our
          hosts. Nobody else. We do not sell or share your data.
        </p>

        <h2 className={h2}>Terms</h2>
        <h3 className={h3}>Your account</h3>
        <p className={p}>
          One person per account. You are responsible for what you file. Do not upload
          another person&rsquo;s records unless you are authorised to act for them — if
          you are, say so on the case, because it changes what your filing must contain.
        </p>
        <h3 className={h3}>Payment</h3>
        <p className={p}>
          The free check, opening a case, uploading your letter, confirming the facts,
          and seeing your route with its real deadlines and citations are free and stay
          free. Writing and exporting the appeal letter is the paid part. If you stop
          paying, your deadlines, your reminders and any letter you already generated
          stay available: we are not going to take away the thing you were relying on.
        </p>
        <h3 className={h3}>No promise about outcomes</h3>
        <p className={p}>
          We do not predict whether your appeal will succeed, and we will never tell you
          that it is likely to. Published figures about appeals in general are facts
          about appeals in general. Nobody can give you a prediction about your case,
          and anybody who offers you one is selling you something.
        </p>
        <h3 className={h3}>Liability</h3>
        <p className={p}>
          We provide this tool as it is. We are not liable for the outcome of an appeal,
          for a deadline you miss, or for a decision you make on the basis of what we
          show you. You review everything before you file it, which is the point at
          which errors are meant to be caught.
        </p>

        <h2 className={h2}>Rules changelog</h2>
        <p className={p}>
          Every conclusion we show you records the version of the rulebase that
          produced it, so any date can be reproduced against the exact rules in force
          when we worked it out.
        </p>
        <div className="rounded-[2px] border border-rule bg-surface p-5">
          <div className={label}>VERSION 1.0.0</div>
          <p className="mt-2 mb-0 text-pretty text-[16px] leading-[26px] text-ink">
            Federal baseline for ACA marketplace and fully-insured employer plans:
            internal appeal filing window, insurer response windows, external review
            request and decision windows, required filing elements. Transcribed from
            45 CFR 147.136 and 29 CFR 2560.503-1.{" "}
            <strong>Every value is marked unverified</strong> — transcribed, but not yet
            checked against its source by a person. State overrides for California, New
            York and Texas are wired and deliberately empty: with no override the
            federal baseline governs, which is honest, and we will not invent a state
            deadline.
          </p>
        </div>

        <p className="mt-12 mb-0 border-t border-rule pt-5 text-pretty text-[14px] leading-[23px] text-ink">
          {DISCLAIMER}
        </p>
      </main>
    </div>
  );
}
