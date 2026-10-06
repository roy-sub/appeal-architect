import { Faq } from "@/components/landing/faq";
import { Hero, Marquee, SiteNav } from "@/components/landing/hero";
import { Capabilities, ClosingCall, Personas, Pricing, Process, SiteFooter, Stats } from "@/components/landing/sections";

export default function LandingPage() {
  return (
    <div className="min-h-full bg-ground">
      <SiteNav />
      <main>
        <Hero />
        <Marquee />
        <Stats />
        <Process />
        <Capabilities />
        <Personas />
        <Pricing />
        <Faq />
        <ClosingCall />
      </main>
      <SiteFooter />
    </div>
  );
}
