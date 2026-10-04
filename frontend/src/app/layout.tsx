import type { Metadata } from "next";
import { Aladin, Barlow_Condensed, Outfit, Shojumaru, Space_Grotesk } from "next/font/google";
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
  const fonts = [spaceGrotesk, outfit, shojumaru, aladin, barlowCondensed];
  return (
    <html lang="en" className={`${fonts.map((font) => font.variable).join(" ")} antialiased`}>
      <body className="min-h-full font-sans">{children}</body>
    </html>
  );
}
