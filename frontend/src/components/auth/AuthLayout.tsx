import type { ReactNode } from "react";

import { Navbar } from "@/components/home/Navbar";

import { PhotoRibbons } from "./PhotoRibbons";

type AuthLayoutProps = {
  title: ReactNode;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
};

/** Shared full-screen frame for the log in and register pages: rows of student photos slide sideways across a
 *  dark purple background (PhotoRibbons) and the form sits in a white card in the middle. Like the home hero,
 *  the page runs up under the floating header; the negative margin is the header's height. */
export function AuthLayout({ title, subtitle, children, footer }: AuthLayoutProps) {
  return (
    <>
      {/* No main link is the current page on the log in and register pages. */}
      <Navbar currentPath="" />
      <main className="relative isolate -mt-[115px] flex min-h-svh items-center justify-center overflow-hidden bg-[#241a5e] px-4 pb-20 pt-[140px] font-body sm:pb-16 lg:-mt-[75px] lg:pt-[110px]">
        <PhotoRibbons />
        {/* Darkens the middle so the photos behind the card don't compete with the form. */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_46%_60%_at_50%_55%,rgba(36,26,94,0.82)_0%,rgba(36,26,94,0.35)_60%,rgba(36,26,94,0.1)_100%)]"
        />

        <div className="w-full max-w-[480px] rounded-[28px] bg-white px-6 pb-8 pt-9 shadow-[0_50px_90px_-40px_rgba(0,0,0,0.75)] sm:px-9">
          <p className="inline-flex items-center gap-2 rounded-full border border-[#e4dcff] bg-[#f7f4ff] px-3.5 py-1.5 text-[13px] font-bold text-[#4a2fd0]">
            <span aria-hidden="true" className="size-2 rounded-full bg-[#6d4aff]" />
            AI-Powered Career Readiness Platform
          </p>
          <h1 className="mt-3.5 font-editorial text-[clamp(36px,4vw,44px)] font-semibold leading-[1.04] tracking-[-0.02em]">
            {title}
          </h1>
          <p className="mb-6 mt-2 text-[16.5px] leading-normal text-[#5c5a55]">{subtitle}</p>
          {children}
          <p className="mt-6 text-center text-[15px] text-[#5c5a55]">{footer}</p>
        </div>
      </main>
    </>
  );
}
