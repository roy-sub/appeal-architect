import Link from "next/link";
import { MediaSlot } from "@/components/media-slot";
import { StatusPill } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import { Bullets, PageHead, card, label, stack } from "@/components/workspace/shell";
import { photoTips, uploadDocs } from "@/lib/case-data";
import { cn } from "@/lib/utils";

export default function DocumentsPage() {
  return (
    <div>
      <PageHead title="Add your documents" lead="Only the denial letter is required. Everything else makes the appeal stronger, and you can add it later." />
      <div className="grid items-start gap-6 lg:grid-cols-[7fr_5fr] lg:gap-8">
        <div className="flex min-w-0 flex-col gap-5">
          <div className="flex flex-col items-center gap-3.5 rounded-[16px] border-[1.5px] border-dashed border-rule bg-surface px-5 py-7 text-center lg:px-10 lg:py-12">
            <div className="w-24">
              <MediaSlot slotId="upload-icon" ratio="1 / 1" kind="illustration" label="A page being placed into a folder" intrinsic="512×512" className="p-2 [&_div]:text-[9px]" />
            </div>
            <h2 className="m-0 text-[19px] leading-[26px] font-semibold text-ink">Drop the letter here, or take a photo</h2>
            <p className="m-0 max-w-[46ch] text-[15px] leading-6 text-ink-muted text-pretty">
              PDF, JPG or PNG. Photograph every page, including the back. Flat light, all four corners in frame.
            </p>
            <div className="flex flex-wrap justify-center gap-2.5">
              <Button asChild>
                <label className="cursor-pointer">
                  Choose a file
                  <input type="file" accept="application/pdf,image/jpeg,image/png" multiple className="sr-only" />
                </label>
              </Button>
              <Button variant="ghost" asChild>
                <label className="cursor-pointer">
                  Use the camera
                  <input type="file" accept="image/*" capture="environment" className="sr-only" />
                </label>
              </Button>
            </div>
          </div>
          <div className={stack}>
            {uploadDocs.map((d) => (
              <div key={d.t} className={cn(card, "flex items-start justify-between gap-4 px-5 py-[18px]")}>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <span className="text-[17px] font-semibold text-ink">{d.t}</span>
                    <StatusPill kind={d.st === "done" ? "solid" : "plain"}>{d.req}</StatusPill>
                  </div>
                  <p className="mt-1.5 mb-0 text-[15px] leading-[23px] text-ink-muted text-pretty">{d.note}</p>
                  <div className="mt-2 font-mono text-[11px] text-ink-muted">{d.meta}</div>
                  {d.st === "uploading" && (
                    <div className="mt-2.5 h-0.5 overflow-hidden rounded-[2px] bg-rule" role="progressbar" aria-valuenow={62} aria-valuemin={0} aria-valuemax={100}>
                      <div className="h-full w-[62%] bg-ink" />
                    </div>
                  )}
                </div>
                <Button variant="small">{d.st === "done" ? "Replace" : d.st === "uploading" ? "Cancel" : "Add"}</Button>
              </div>
            ))}
          </div>
        </div>
        <div className={card}>
          <div className="p-[22px]">
            <div className={cn(label, "mb-3.5")}>Photographing it on a phone</div>
            <div className="mb-[18px]">
              <MediaSlot slotId="camera-guide" ratio="3 / 4" kind="image" label="A denial letter framed correctly in a phone camera, with edge guides" intrinsic="900×1200" />
            </div>
            <Bullets items={photoTips} />
            <p className="mt-[18px] mb-0 border-t border-rule pt-4 text-[14px] leading-[22px] text-ink-muted">
              Your files are encrypted and stored against this case. They are not shared with your insurer and never used to train anything.
            </p>
          </div>
        </div>
      </div>
      <div className="mt-6 flex flex-wrap gap-3">
        <Button asChild><Link href="/case/facts/">Read the letter</Link></Button>
        <Button variant="ghost" asChild><Link href="/cases/">Save and come back</Link></Button>
      </div>
    </div>
  );
}
