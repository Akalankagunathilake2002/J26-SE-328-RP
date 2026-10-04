import type { ReactNode } from "react";

import { Navbar } from "@/components/home/Navbar";
import { SparkleDoodle } from "@/components/icons";

type AuthLayoutProps = {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
};

/** Shared frame for the login and register pages, in the style of the home page hero. */
export function AuthLayout({ title, subtitle, children, footer }: AuthLayoutProps) {
  return (
    <>
      <Navbar />
      <main className="hero-grid relative min-h-[calc(100vh-64px)] px-4 pb-24 pt-16">
        <span
          aria-hidden="true"
          className="absolute left-5 top-0 h-[60px] w-[53px] bg-white [clip-path:polygon(0_0,100%_0,100%_100%,50%_68%,0_100%)]"
        />
        <div className="mx-auto w-full max-w-[480px]">
          <h1 className="font-display text-[38px] uppercase leading-[1.15] text-white text-block-shadow sm:text-[46px]">
            {title}
          </h1>
          <p className="mt-3 text-[18px] font-medium text-white">{subtitle}</p>

          <div className="relative mt-8">
            {/* Stacked paper layers behind the card, as on the home page */}
            <div aria-hidden="true" className="absolute inset-0 translate-x-[22px] translate-y-[22px] bg-ink" />
            <div aria-hidden="true" className="absolute inset-0 translate-x-[12px] translate-y-[12px] border-[2.5px] border-ink bg-cyan" />
            <div className="relative border-[2.5px] border-ink bg-cream px-6 py-8 sm:px-8">
              {children}
              <p className="mt-6 text-center text-[15px]">{footer}</p>
            </div>
            <SparkleDoodle aria-hidden="true" className="absolute -bottom-12 -right-10 w-[34px] text-lime" />
          </div>
        </div>
      </main>
    </>
  );
}
