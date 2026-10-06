import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

// Every button is ≥44px tall (touch-target floor). Marketing surfaces use the
// sharp 2px radius; the workspace uses 10px / 8px. A disabled button must always
// have its reason stated in adjacent text (components.md § Button).
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors duration-[180ms] disabled:cursor-not-allowed disabled:opacity-45 aria-disabled:cursor-not-allowed aria-disabled:opacity-45",
  {
    variants: {
      variant: {
        primary: "min-h-[46px] rounded-[10px] bg-ink px-5 py-[13px] text-[16px] font-medium text-ground hover:bg-[#2c2924]",
        ghost: "min-h-[44px] rounded-[10px] border border-rule bg-surface px-4 py-[11px] text-[15px] text-ink hover:border-ink-muted",
        small: "min-h-[44px] rounded-[8px] border border-rule bg-surface px-[13px] py-[9px] text-[14px] text-ink hover:border-ink-muted",
        inkSmall: "min-h-[44px] rounded-[8px] bg-ink px-[13px] py-[9px] text-[14px] font-medium text-ground hover:bg-[#2c2924]",
        nav: "h-[44px] rounded-[2px] bg-ink px-5 text-[14px] font-medium text-ground hover:bg-[#2c2924]",
        clay: "h-[52px] rounded-[2px] bg-clay px-[26px] text-[15px] font-medium text-paper hover:bg-clay-deep",
        heroGhost: "h-[52px] rounded-[2px] border border-paper/30 bg-transparent px-[26px] text-[15px] font-medium text-paper hover:border-paper/60",
        invert: "h-[54px] rounded-[2px] bg-paper px-[30px] text-[15px] font-semibold text-clay-deep hover:bg-ground",
        clayBlock: "h-[50px] w-full rounded-[2px] bg-clay text-[15px] font-medium text-paper hover:bg-clay-deep",
        outlineBlock: "h-[50px] w-full rounded-[2px] border border-ink bg-transparent text-[15px] font-medium text-ink hover:bg-ink hover:text-ground",
      },
    },
    defaultVariants: { variant: "primary" },
  },
);

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export function Button({ className, variant, asChild = false, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  return <Comp className={cn(buttonVariants({ variant }), className)} {...props} />;
}

export { buttonVariants };
