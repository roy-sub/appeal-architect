import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Newsreader } from "next/font/google";
import { MotionProvider } from "@/components/motion-provider";
import { Providers } from "./providers";
import "./globals.css";

const sans = IBM_Plex_Sans({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--font-plex-sans", display: "swap" });
const mono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-plex-mono", display: "swap" });
const doc = Newsreader({ subsets: ["latin"], weight: ["400", "500", "600"], style: ["normal", "italic"], variable: "--font-newsreader", display: "swap" });

export const metadata: Metadata = {
  title: "Appeal Architect — Your denial, formally refuted.",
  description: "Every paragraph backed by a rule. Find your appeal track, your deadline, and the arguments that hold against your health-insurance denial.",
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
