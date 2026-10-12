import type { Metadata } from "next";

// The triage page itself is a client component, so its metadata lives here.
// This is the page most people arrive on from search, so it gets its own title
// and description rather than inheriting the site's.
export const metadata: Metadata = {
  title: "Find your appeal deadline — Appeal Architect",
  description:
    "Four questions, no account, nothing stored. Find which appeal track your plan puts you on, when your window closes, and the regulation that sets it.",
  alternates: { canonical: "/triage/" },
};

export default function TriageLayout({ children }: { children: React.ReactNode }) {
  return children;
}
