import type { Metadata } from "next";

import { ComingSoon } from "@/components/pages/ComingSoon";

export const metadata: Metadata = { title: "Market Pulse — Skillaro" };

export default function MarketPulsePage() {
  return (
    <ComingSoon
      path="/market-pulse"
      title="Market Pulse"
      description="Explore real market signals to understand emerging roles, in-demand skills, and salary trends."
    />
  );
}
