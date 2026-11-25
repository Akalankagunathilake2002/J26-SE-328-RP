import type { Metadata } from "next";
import { Aladin, Barlow_Condensed, Outfit, Shojumaru, Space_Grotesk } from "next/font/google";
import { figtree, fraunces } from "@/components/home/fonts";

import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
});

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
});

const shojumaru = Shojumaru({
  variable: "--font-shojumaru",
  subsets: ["latin"],
  weight: "400",
});

const aladin = Aladin({
  variable: "--font-aladin",
  subsets: ["latin"],
  weight: "400",
});

const barlowCondensed = Barlow_Condensed({
  variable: "--font-barlow-condensed",
  subsets: ["latin"],
  weight: ["600", "700"],
});

export const metadata: Metadata = {
  title: "Skillaro — Bridge what you know with what industry needs",
  description:
    "Understand your skills, discover the gaps, and get a personalized path to become career ready.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  // Fraunces (headings) and Figtree (text) give every page the home page look; the older fonts stay loaded
  // for anything that still names them directly.
  const fonts = [fraunces, figtree, spaceGrotesk, outfit, shojumaru, aladin, barlowCondensed];
  return (
    <html lang="en" className={`${fonts.map((font) => font.variable).join(" ")} antialiased`}>
      <body className="min-h-full bg-page font-sans text-[#141413]">{children}</body>
    </html>
  );
}
