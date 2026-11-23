import { Figtree, Fraunces } from "next/font/google";

// Fonts for the home page only; the rest of the site keeps the root layout's fonts.
// Used through the font-editorial and font-body utilities in globals.css.

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
