"use client";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";
import { useCheckout } from "@/lib/hooks";

/** The one way to pay. Nothing else in the app calls checkout.
 *
 *  Payment can fail for a reason the person can act on (the server has no
 *  Stripe keys) and for one they cannot (Stripe refused), so the error is shown
 *  where the button is rather than swallowed. Nothing is charged in either case,
 *  and the button says so.
 */
export function BuyButton({
  product = "appeal_package",
  children,
  variant,
}: {
  product?: "appeal_package" | "subscription";
  children: React.ReactNode;
  variant?: "primary" | "ghost" | "small" | "inkSmall";
}) {
  const checkout = useCheckout();
  const problem = checkout.error instanceof ApiError ? checkout.error.problem : null;

  return (
    <div>
      <Button
        variant={variant}
        onClick={() => checkout.mutate(product)}
        disabled={checkout.isPending || checkout.isSuccess}
      >
        {checkout.isPending || checkout.isSuccess ? "Opening the payment page…" : children}
      </Button>
      {checkout.isError ? (
        <p className="mt-2.5 mb-0 max-w-[52ch] border-l-[3px] border-ink pl-3 text-[15px] leading-[24px] text-ink text-pretty">
          {problem?.detail ?? "We could not open the payment page just now."} Nothing was
          charged.
        </p>
      ) : null}
    </div>
  );
}
