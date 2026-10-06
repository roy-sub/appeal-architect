"use client";
import * as Dialog from "@radix-ui/react-dialog";
import { cn } from "@/lib/utils";

export const Sheet = Dialog.Root;
export const SheetTitle = Dialog.Title;
export const SheetDescription = Dialog.Description;
export const SheetClose = Dialog.Close;

// Right-hand drawer: full width on phones, 460px on desktop.
export function SheetContent({ className, children, ...props }: React.ComponentProps<typeof Dialog.Content>) {
  return (
    <Dialog.Portal>
      <Dialog.Overlay className="fixed inset-0 z-[55] bg-[var(--overlay)] animate-fade" />
      <Dialog.Content
        className={cn(
          "fixed inset-y-0 right-0 z-[60] w-full overflow-y-auto border-l border-rule bg-surface p-5 shadow-e2 animate-fade focus:outline-none lg:w-[460px] lg:p-7",
          className,
        )}
        {...props}
      >
        {children}
      </Dialog.Content>
    </Dialog.Portal>
  );
}
