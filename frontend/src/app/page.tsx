import { Footer } from "@/components/home/Footer";
import { Hero } from "@/components/home/Hero";
import { IndustrySection, PracticeSection, ProveSection, StandSection } from "@/components/home/FeatureSections";
import { Navbar } from "@/components/home/Navbar";
import { StatsBar } from "@/components/home/StatsBar";

export default function HomePage() {
  return (
    <>
      <Navbar />
      <main className="overflow-x-clip">
        <Hero />
        <StatsBar />
        <IndustrySection />
        <ProveSection />
        <StandSection />
        <PracticeSection />
      </main>
      <Footer />
    </>
  );
}
