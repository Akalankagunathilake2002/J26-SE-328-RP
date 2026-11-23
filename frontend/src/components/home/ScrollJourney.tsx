"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

/** One young man (free Pexels photos by Pavel Danilyuk, cut out with Apple Vision) in six moods, from lost
 *  to career ready. */
const stages = [
  "/journey/guy-1.png", // doesn't know his gaps
  "/journey/guy-2.png", // finds his gaps
  "/journey/guy-3.png", // learns
  "/journey/guy-4.png", // practises
  "/journey/guy-5.png", // grows
  "/journey/guy-6-career.png", // career ready: his head (Pexels 8422379) on a suit photo (Pexels 20715518), black and white
];

/** The student stands in the bottom-right corner of the home page and changes as the visitor scrolls: lost at
 *  the top, then finding his gaps, learning, practising, growing, and celebrating at the footer. He also
 *  grows a little taller. Decorative only, so it is hidden from screen readers and lets clicks through. */
export function ScrollJourney() {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    let frame = 0;
    const update = () => {
      frame = 0;
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const progress = max > 0 ? window.scrollY / max : 0;
      setStage(Math.min(stages.length - 1, Math.floor(progress * stages.length)));
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    frame = requestAnimationFrame(update);
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <div aria-hidden="true" className="pointer-events-none fixed bottom-0 right-0 z-40">
      {/* He gets a little taller with every stage. */}
      <div
        className="relative h-[230px] w-[215px] origin-bottom-right transition-transform duration-700 ease-out motion-reduce:transition-none sm:h-[340px] sm:w-[330px] lg:h-[min(480px,58vh)] lg:w-[min(470px,57vh)]"
        style={{ transform: `scale(${0.86 + (0.14 * stage) / (stages.length - 1)})` }}
      >
        {stages.map((src, i) => (
          <Image
            key={src}
            src={src}
            alt=""
            fill
            sizes="(min-width: 1024px) 470px, (min-width: 640px) 330px, 215px"
            loading="eager"
            className={`object-contain object-[85%_100%] drop-shadow-[0_12px_18px_rgba(20,15,40,0.28)] transition-[opacity,transform] duration-700 ease-out motion-reduce:transition-none ${
              i === stage ? "translate-y-0 opacity-100" : "translate-y-5 opacity-0"
            }`}
          />
        ))}
      </div>
    </div>
  );
}
