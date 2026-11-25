import { Figtree, Fraunces } from "next/font/google";

// The site's fonts (loaded in the root layout): Fraunces for headings, Figtree for text.
// Used through font-editorial / font-body, and font-sans / font-display / font-script map to them too (globals.css).

export const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
  weight: "600",
  style: ["normal", "italic"],
});

export const figtree = Figtree({
  variable: "--font-figtree",
  subsets: ["latin"],
});
