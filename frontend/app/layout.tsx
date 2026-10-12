import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Newsreader } from "next/font/google";
import { MotionProvider } from "@/components/motion-provider";
import { SITE_URL } from "@/lib/site-url";
import { Providers } from "./providers";
import "./globals.css";

const sans = IBM_Plex_Sans({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--font-plex-sans", display: "swap" });
const mono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-plex-mono", display: "swap" });
const doc = Newsreader({ subsets: ["latin"], weight: ["400", "500", "600"], style: ["normal", "italic"], variable: "--font-newsreader", display: "swap" });

const DESCRIPTION =
  "Every paragraph backed by a rule. Find your appeal track, your deadline, and the arguments that hold against your health-insurance denial.";

export const metadata: Metadata = {
  // Absolute URLs are built from this. Unset, Next uses localhost and the share
  // card silently points nowhere.
  metadataBase: new URL(SITE_URL),
  alternates: { canonical: "/" },
  title: "Appeal Architect — Your denial, formally refuted.",
  description: DESCRIPTION,
  // The share card lives at public/media/og-card.png: 1200x630, the size every
  // scraper expects. PNG rather than webp because some crawlers still skip webp.
  openGraph: {
    title: "Appeal Architect — Your denial, formally refuted.",
    description: DESCRIPTION,
    type: "website",
    images: [{ url: "/media/og-card.png", width: 1200, height: 630 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Appeal Architect — Your denial, formally refuted.",
    description: DESCRIPTION,
    images: ["/media/og-card.png"],
  },
};

export const viewport: Viewport = { width: "device-width", initialScale: 1, themeColor: "#F2EDE4" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="light" className={`${sans.variable} ${mono.variable} ${doc.variable}`}>
      <body className="min-h-dvh antialiased">
        <Providers>
          <MotionProvider>{children}</MotionProvider>
        </Providers>
      </body>
    </html>
  );
}
