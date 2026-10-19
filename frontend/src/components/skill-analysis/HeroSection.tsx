import Image from "next/image";

// Hero section combining title, descriptive text, girl illustration, and speech bubble
export function HeroSection() {
  return (
    <section className="relative pt-4 sm:pt-6 pb-0">
      <div className="grid grid-cols-1 md:grid-cols-[1.1fr_1.2fr] items-end gap-6 md:gap-4">
        {/* Left column: Title and value proposition */}
        <div className="pb-4 md:pb-6 z-10">
          <div className="relative inline-block">
            {/* Small decorative sparkle */}
            <span
              aria-hidden="true"
              className="absolute -left-6 -top-2 text-sun text-2xl select-none"
            >
              ✦
            </span>
            <h1 className="font-extrabold text-3xl sm:text-4xl lg:text-5xl text-ink tracking-tight leading-[1.1]">
              Career Readiness <br />
              Analysis
            </h1>
          </div>
          <p className="mt-3 text-sm sm:text-base text-ink/75 font-medium max-w-md leading-relaxed">
            See how your skills align with your selected role and discover your path to growth.
          </p>
        </div>

        {/* Right column: Illustration with interactive speech bubble */}
        <div className="relative flex justify-center md:justify-end items-end">
          {/* Editable speech bubble positioned above the character */}
          <div className="absolute -top-14 right-2 sm:right-6 md:right-4 z-20 max-w-[210px] sm:max-w-[230px]">
            <div className="relative bg-[#edddfc] border-2 border-ink rounded-2xl px-4 py-2.5 shadow-[3px_3px_0px_#000]">
              <p className="font-bold text-xs sm:text-sm text-ink leading-snug">
                Let&apos;s see how ready you are for your dream role!
              </p>
              {/* Speech bubble tail pointing towards character */}
              <div
                aria-hidden="true"
                className="absolute -bottom-2 left-6 size-3.5 bg-[#edddfc] border-b-2 border-l-2 border-ink -rotate-45"
              />
            </div>
          </div>

          {/* Girl at desk illustration touching Start Analysis card */}
          <div className="relative w-full max-w-[360px] sm:max-w-[420px] aspect-[1873/804] -mb-[2px] z-10">
            <Image
              src="/readiness-analysis/readiness-illustration.png"
              alt="Student preparing for career readiness analysis"
              fill
              priority
              className="object-contain object-bottom"
              sizes="(max-width: 640px) 340px, (max-width: 768px) 400px, 440px"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
