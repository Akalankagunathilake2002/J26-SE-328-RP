import Link from "next/link";

import { Navbar } from "@/components/home/Navbar";
import { ArrowRightIcon } from "@/components/icons";
import { requireUser } from "@/lib/auth";

type ComingSoonProps = {
  path: string;
  title: string;
  description: string;
};

/** Placeholder for a logged-in page that hasn't been built yet. */
export async function ComingSoon({ path, title, description }: ComingSoonProps) {
  const user = await requireUser(path);
  const firstName = user.full_name.split(" ")[0];

  return (
    <>
      <Navbar currentPath={path} />
      <main className="hero-grid min-h-[calc(100vh-64px)] px-4 pb-24 pt-16">
        <div className="mx-auto w-full max-w-[640px]">
          <p className="inline-block border-2 border-ink bg-pink px-[15px] py-[2px] font-condensed text-[17px] font-semibold uppercase leading-[23px]">
            Hi {firstName}
          </p>
          <h1 className="mt-5 font-display text-[38px] uppercase leading-[1.15] text-white text-block-shadow sm:text-[52px]">
            {title}
          </h1>

          <div className="relative mt-8">
            <div aria-hidden="true" className="absolute inset-0 translate-x-[22px] translate-y-[22px] bg-ink" />
            <div aria-hidden="true" className="absolute inset-0 translate-x-[12px] translate-y-[12px] border-[2.5px] border-ink bg-cyan" />
            <div className="relative border-[2.5px] border-ink bg-cream px-6 py-8 sm:px-10">
              <p className="text-[20px] leading-[1.6] sm:text-[24px]">{description}</p>
              <p className="mt-6 font-semibold text-brand-blue">This page is coming soon.</p>
              <Link
                href="/"
                className="hard-shadow mt-8 inline-flex h-12 items-center gap-3 bg-lime px-6 font-semibold transition-transform hover:-translate-y-0.5"
              >
                Back to home
                <ArrowRightIcon className="size-5" />
              </Link>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
