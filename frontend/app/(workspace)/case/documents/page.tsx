"use client";

import Link from "next/link";
import { useRef, useState } from "react";

import { MediaSlot } from "@/components/media-slot";
import { Button } from "@/components/ui/button";
import { PageHead, card, label, well } from "@/components/workspace/shell";
import { useCase } from "@/components/workspace/case-context";
import { LoadError, NeedsCase, Stages } from "@/components/workspace/states";
import type { DocumentKind } from "@/lib/api";
import { useDocuments, useUploadDocument } from "@/lib/hooks";
import { cn } from "@/lib/utils";

/** The stages shown while a document is read. Named, not a spinner. */
const READING_STAGES = [
  "Uploading your file",
  "Reading the pages",
  "Finding the reason codes",
  "Matching your plan type",
];

const KINDS: { value: DocumentKind; label: string; hint: string }[] = [
  {
    value: "denial_letter",
    label: "Denial letter",
    hint: "Start here. Every page, including the back.",
  },
  {
    value: "eob",
    label: "Explanation of benefits",
    hint: "Useful, not required.",
  },
  {
    value: "plan_doc",
    label: "Plan document",
    hint: "The clinical policy pages, if you have them.",
  },
  {
    value: "medical_record",
    label: "Medical records",
    hint: "Chart notes that show the clinical picture.",
  },
  {
    value: "physician_letter",
    label: "Physician letter",
    hint: "Your doctor's written support.",
  },
];

export default function DocumentsPage() {
  const { caseId } = useCase();
  const documents = useDocuments(caseId);
  const upload = useUploadDocument(caseId);
  const fileInput = useRef<HTMLInputElement>(null);
  const cameraInput = useRef<HTMLInputElement>(null);
  const [kind, setKind] = useState<DocumentKind>("denial_letter");
  const [stage, setStage] = useState(0);

  if (!caseId) return <NeedsCase />;

  async function send(file: File | undefined) {
    if (!file) return;
    setStage(0);
    // The stages advance on a timer rather than from real progress: the backend
    // does the work in one request. The sequence is honest about what is
    // happening even though it cannot be precise about when.
    const timers = [
      setTimeout(() => setStage(1), 900),
      setTimeout(() => setStage(2), 3200),
      setTimeout(() => setStage(3), 6500),
    ];
    try {
      await upload.mutateAsync({ file, kind });
    } finally {
      timers.forEach(clearTimeout);
      setStage(0);
    }
  }

  const reading = upload.isPending;

  return (
    <div>
      <PageHead
        title="Start with the denial letter"
        lead="We read it, pull out the facts, and show you each one next to the sentence it came from. You confirm or correct every one before anything is worked out."
      />

      {reading ? (
        <Stages
          stages={READING_STAGES}
          active={stage}
          note="A scanned page takes longer than a PDF, because we transcribe it a page at a time. You can close this page."
        />
      ) : (
        <>
          <div className={cn(card, "p-[22px]")}>
            <div className={cn(label, "mb-3")}>What is this document</div>
            <div className="flex flex-wrap gap-2">
              {KINDS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setKind(option.value)}
                  className={cn(
                    "min-h-[44px] rounded-[8px] border px-3.5 text-[15px] transition-colors",
                    kind === option.value
                      ? "border-ink bg-forest-tint font-medium text-ink"
                      : "border-rule bg-surface text-ink-muted hover:border-ink-muted",
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <p className="mt-2.5 mb-0 text-[14px] leading-[22px] text-ink-muted">
              {KINDS.find((k) => k.value === kind)?.hint}
            </p>
          </div>

          <div className="mt-3.5 grid gap-3.5 lg:grid-cols-[1fr_320px]">
            {/* ---- the drop zone ---- */}
            <div
              className="flex flex-col items-center gap-4 rounded-[16px] border-[1.5px] border-dashed border-rule bg-surface px-7 py-12 text-center"
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                void send(e.dataTransfer.files?.[0]);
              }}
            >
              <div className="w-[88px]">
                <MediaSlot
                  slotId="upload-icon"
                  ratio="1 / 1"
                  kind="illustration"
                  label="A page being placed into a folder"
                  intrinsic="512×512"
                  className="p-2 [&_div]:text-[9px]"
                />
              </div>
              <h2 className="m-0 text-[19px] leading-7 font-semibold text-ink">
                Drop the file here, or choose it
              </h2>
              <p className="m-0 max-w-[40ch] text-pretty text-[15px] leading-[24px] text-ink-muted">
                A PDF, or a photo of each page. Up to 25 MB and 30 pages.
              </p>

              <input
                ref={fileInput}
                type="file"
                accept="application/pdf,image/png,image/jpeg,image/webp"
                className="sr-only"
                onChange={(e) => void send(e.target.files?.[0])}
              />
              <input
                ref={cameraInput}
                type="file"
                accept="image/*"
                capture="environment"
                className="sr-only"
                onChange={(e) => void send(e.target.files?.[0])}
              />

              <div className="flex flex-wrap justify-center gap-3">
                <Button onClick={() => fileInput.current?.click()}>Choose a file</Button>
                {/* Camera capture is the mobile path the brief calls first-class. */}
                <Button
                  variant="ghost"
                  className="lg:hidden"
                  onClick={() => cameraInput.current?.click()}
                >
                  Take a photo
                </Button>
              </div>

              <p className="m-0 max-w-[46ch] text-pretty text-[13px] leading-[21px] text-ink-muted">
                The file is encrypted and stored privately. We send the text to an AI
                model to read it, and we never log what was sent.
              </p>
            </div>

            {/* ---- how to photograph it well ---- */}
            <div className={cn(card, "p-5")}>
              <div className={cn(label, "mb-3")}>Photographing a letter</div>
              <MediaSlot
                slotId="camera-guide"
                ratio="3 / 4"
                kind="image"
                label="A denial letter framed correctly in a phone camera"
                intrinsic="900×1200"
              />
              <ul className="mt-4 mb-0 flex list-none flex-col gap-2 p-0">
                {[
                  "Flatten the page and get all four corners in frame.",
                  "Daylight if you can. Avoid your own shadow.",
                  "One photo per page, including the back.",
                ].map((tip) => (
                  <li key={tip} className="text-[15px] leading-[23px] text-ink-muted">
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </>
      )}

      {upload.isError ? (
        <div className="mt-3.5">
          <LoadError error={upload.error} what="that file" />
        </div>
      ) : null}

      {upload.isSuccess && !reading ? (
        <div className="mt-3.5 border-l-[3px] border-standing bg-surface px-[18px] py-4">
          <p className="m-0 text-[16px] leading-[26px] text-ink">
            Read {upload.data.document.filename} —{" "}
            {upload.data.document.page_count ?? 1}{" "}
            {upload.data.document.page_count === 1 ? "page" : "pages"},{" "}
            {upload.data.facts_proposed}{" "}
            {upload.data.facts_proposed === 1 ? "fact" : "facts"} to check.
            {upload.data.pages_transcribed > 0
              ? ` ${upload.data.pages_transcribed} ${
                  upload.data.pages_transcribed === 1 ? "page was" : "pages were"
                } transcribed from a scan, so look at those especially closely.`
              : ""}
          </p>
          <Button asChild className="mt-3.5">
            <Link href="/case/facts/">Check what we read</Link>
          </Button>
        </div>
      ) : null}

      {/* ---- what is already on file ---- */}
      <div className="mt-7">
        <div className="mb-3.5 flex items-baseline gap-3.5">
          <span className={cn(label, "whitespace-nowrap")}>On file</span>
          <span className="h-px flex-1 bg-rule" />
        </div>
        {documents.isPending ? (
          <p className="m-0 text-[15px] text-ink-muted">Checking…</p>
        ) : documents.isError ? (
          <LoadError
            error={documents.error}
            what="your documents"
            onRetry={() => documents.refetch()}
          />
        ) : documents.data.length === 0 ? (
          <p className="m-0 text-[15px] leading-[24px] text-ink-muted">
            Nothing yet. The denial letter is the one that matters most.
          </p>
        ) : (
          <ul className="m-0 flex list-none flex-col gap-2.5 p-0">
            {documents.data.map((document) => (
              <li key={document.id} className={cn(well, "flex flex-wrap items-center gap-3")}>
                <span className="flex-1 text-[16px] text-ink">{document.filename}</span>
                <span className="font-mono text-[11px] text-ink-muted">
                  {document.page_count ?? 1}{" "}
                  {document.page_count === 1 ? "PAGE" : "PAGES"}
                </span>
                {document.ocr_used ? (
                  <span className="font-mono text-[11px] text-time">TRANSCRIBED</span>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
