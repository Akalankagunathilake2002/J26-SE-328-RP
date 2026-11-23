import { FileCheck, Network, Newspaper, ShieldCheck } from "lucide-react";
import Link from "next/link";

import { ArrowRightIcon } from "@/components/icons";

import { FaqSection } from "./FaqSection";
import { Reveal } from "./Reveal";

const trust = [
  {
    icon: FileCheck,
    title: "Evidence-backed profile",
    text: "Your skills come from your CV, projects, certificates and GitHub, each with a confidence score.",
    tone: "bg-[#fff0bf] text-[#5c4200]",
  },
  {
    icon: Newspaper,
    title: "Real job ads, collected fairly",
    text: "We follow each job site's rules, skip sites that don't allow it and never keep personal details.",
    tone: "bg-[#efe8ff] text-[#3b2394]",
  },
  {
    icon: Network,
    title: "One shared skill dictionary",
    text: "1,800+ skills with verified links between them, so every part of Skillaro speaks the same language.",
    tone: "bg-[#dbeeff] text-[#0b4a80]",
  },
  {
    icon: ShieldCheck,
    title: "Your data stays yours",
    text: "Interview recordings go straight to your own Google Drive, never to our servers.",
    tone: "bg-[#ffdcee] text-[#7a1048]",
  },
];

const faqs = [
  {
    q: "What is Skillaro?",
    a: "Skillaro helps students see what employers ask for, build a skill profile from real evidence, find their skill gaps and practise for interviews, all in one place.",
  },
  {
    q: "Where does the job data come from?",
    a: "From public job ads on topjobs.lk and itpro.lk, collected every day. We check each site's rules first and skip sites that don't allow it.",
  },
  {
    q: "How is my readiness score worked out?",
    a: "We compare your skills with the skills employers ask for in the role you choose. Skills that appear in more job ads count for more. A related skill counts only when the link between the two skills is verified.",
  },
  {
    q: "What can I use as evidence?",
    a: "Your CV, project reports, academic documents, certificates and GitHub. Each skill shows how strongly your evidence supports it.",
  },
  {
    q: "Are my interview recordings stored?",
    a: "Recording is optional. If you turn it on, the video is saved straight to your own Google Drive and never reaches Skillaro's servers.",
  },
  {
    q: "Do I need an account?",
    a: "Yes. Create an account to build your profile, see Market Pulse and get your readiness report.",
  },
];

/** Why trust Skillaro, the FAQ and a final call to action, before the footer. */
export function ClosingSections() {
  return (
    <>
      <section aria-labelledby="trust-heading" className="mx-auto max-w-[1240px] px-4 py-16 sm:px-8 lg:py-20">
        <Reveal className="text-center">
          <p className="text-[13px] font-extrabold uppercase tracking-[0.12em] text-[#5b3df5]">Why trust Skillaro</p>
          <h2 id="trust-heading" className="mx-auto mt-3 max-w-[640px] font-editorial text-[clamp(32px,3.6vw,46px)] font-semibold leading-[1.08] tracking-[-0.01em]">
            Built on <em className="text-[#5b3df5]">evidence,</em> not guesses.
          </h2>
        </Reveal>
        <ul className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {trust.map(({ icon: Icon, title, text, tone }, i) => (
            <li key={title}>
              <Reveal delay={i * 110} className="h-full">
                <div className="h-full rounded-[22px] border border-[#e6e2da] bg-white p-5 shadow-[0_20px_40px_-30px_rgba(40,30,10,0.5)]">
                  <span aria-hidden="true" className={`grid size-11 place-items-center rounded-2xl ${tone}`}>
                    <Icon className="size-5" />
                  </span>
                  <h3 className="mt-4 font-editorial text-[20px] font-semibold leading-tight">{title}</h3>
                  <p className="mt-1.5 text-[14.5px] text-[#5c5a55]">{text}</p>
                </div>
              </Reveal>
            </li>
          ))}
        </ul>
      </section>

      <FaqSection items={faqs} />

      <section aria-labelledby="cta-heading" className="mx-auto max-w-[1240px] px-4 pt-16 sm:px-8">
        <Reveal>
          <div className="relative overflow-hidden rounded-[30px] bg-linear-to-br from-[#4a2fd0] via-[#6d4aff] to-[#b86bff] px-6 py-12 text-center text-white sm:px-12">
            <div aria-hidden="true" className="absolute -right-16 -top-20 size-64 rounded-full bg-white/10" />
            <div aria-hidden="true" className="absolute -bottom-24 -left-10 size-56 rounded-full bg-[#d0ffa4]/20" />
            <h2 id="cta-heading" className="relative font-editorial text-[clamp(30px,3.6vw,46px)] font-semibold leading-[1.08]">
              Ready to <em className="text-[#d0ffa4]">bridge the gap?</em>
            </h2>
            <p className="relative mx-auto mt-3 max-w-[520px] text-[17px] text-white/85">
              Create your account, add your evidence and see where you stand.
            </p>
            <div className="relative mt-7 flex flex-wrap justify-center gap-3">
              <Link
                href="/register"
                className="inline-flex min-h-12 items-center gap-2 rounded-full bg-white px-7 text-[16px] font-bold text-[#4a2fd0] transition hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-white/50"
              >
                Create your account <ArrowRightIcon className="size-[18px]" strokeWidth={2.4} />
              </Link>
              <Link
                href="/login"
                className="inline-flex min-h-12 items-center rounded-full px-7 text-[16px] font-bold text-white ring-2 ring-white/50 transition hover:bg-white/10 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-white/60"
              >
                Log in
              </Link>
            </div>
          </div>
        </Reveal>
      </section>
    </>
  );
}
