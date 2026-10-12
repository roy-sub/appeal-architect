import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign in — Appeal Architect",
  description: "A sign-in link by email. No password to remember or to lose.",
  alternates: { canonical: "/signin/" },
};

export default function SignInLayout({ children }: { children: React.ReactNode }) {
  return children;
}
