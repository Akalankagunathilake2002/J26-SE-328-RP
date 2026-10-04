/** Main navigation. Every page except Home needs a logged-in user (see src/proxy.ts). */
export const navLinks = [
  { label: "Home", href: "/" },
  { label: "Skills Profile", href: "/skills-profile" },
  { label: "Market Pulse", href: "/market-pulse" },
  { label: "Skill Analysis", href: "/skill-analysis" },
  { label: "Mock Interview", href: "/mock-interview" },
] as const;
