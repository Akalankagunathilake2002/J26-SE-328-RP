import { ClosingSections } from "@/components/home/ClosingSections";
import { figtree, fraunces } from "@/components/home/fonts";
import { Footer } from "@/components/home/Footer";
import { Hero } from "@/components/home/Hero";
import { HowItWorks } from "@/components/home/HowItWorks";
import { MarketTeaser } from "@/components/home/MarketTeaser";
import { Navbar } from "@/components/home/Navbar";
import { PracticePreview } from "@/components/home/PracticePreview";
import { ReadinessPreview } from "@/components/home/ReadinessPreview";
import { Reveal } from "@/components/home/Reveal";
import { ScrollJourney } from "@/components/home/ScrollJourney";
import { StatsBar } from "@/components/home/StatsBar";

export default function HomePage() {
  return (
    <div className={`${fraunces.variable} ${figtree.variable} bg-[#f4f2ee]`}>
      <Navbar variant="soft" />
      <main className="overflow-x-clip font-body text-[#141413]">
        <Hero />
        <Reveal>
          <StatsBar />
        </Reveal>
        <Reveal>
          <HowItWorks />
        </Reveal>
        <MarketTeaser />
        <ReadinessPreview />
        <PracticePreview />
        <ClosingSections />
      </main>
      <Footer />
      <ScrollJourney />
    </div>
  );
}
