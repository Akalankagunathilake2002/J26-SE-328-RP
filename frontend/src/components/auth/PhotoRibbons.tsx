"use client";

import { Pause, Play } from "lucide-react";
import Image from "next/image";
import { useState, useSyncExternalStore } from "react";

/** A ribbon tile is either a photo or a coloured card with one of the home page benefit lines. */
type Tile = { src: string; focus?: string } | { label: string; tone: string };

const photos = {
  library: "/illustrations/faq-1.jpg",
  laptop: "/illustrations/faq-2.jpg",
  laughing: "/illustrations/faq-3.jpg",
  reading: "/illustrations/faq-4.jpg",
  evidence: "/photos/evidence.jpg",
  industry: "/photos/industry.jpg",
  practice: "/photos/practice.jpg",
  stand: "/photos/stand.jpg",
};

// Three rows; the speed classes set --ribbon-speed for the slide animation in globals.css.
const rows: { direction: "left" | "right"; speed: string; tiles: Tile[] }[] = [
  {
    direction: "left",
    speed: "[--ribbon-speed:70s]",
    tiles: [
      { src: photos.laughing },
      { label: "Know what's in demand", tone: "bg-[#6d4aff] text-white" },
      { src: photos.industry },
      { src: photos.evidence },
      { label: "Identify skill gaps", tone: "bg-[#e0407f] text-white" },
      { src: photos.laptop, focus: "object-left" },
      { src: photos.practice },
      { src: photos.stand },
    ],
  },
  {
    direction: "right",
    speed: "[--ribbon-speed:80s]",
    tiles: [
      { src: photos.library },
      { src: photos.practice },
      { label: "Learn what matters", tone: "bg-[#d0ffa4] text-[#145a36]" },
      { src: photos.reading },
      { src: photos.laughing, focus: "object-right" },
      { src: photos.industry },
      { label: "Practice & get feedback", tone: "bg-[#7cc4ff] text-[#0b2f55]" },
      { src: photos.evidence },
    ],
  },
  {
    direction: "left",
    speed: "[--ribbon-speed:60s]",
    tiles: [
      { src: photos.stand },
      { src: photos.laptop },
      { label: "Understand your strengths", tone: "bg-[#ffd84d] text-[#4a3500]" },
      { src: photos.laughing },
      { src: photos.library },
      { label: "Identify skill gaps", tone: "bg-[#efe8ff] text-[#3b2394]" },
      { src: photos.practice },
      { src: photos.reading },
    ],
  },
];

const reducedMotionQuery = "(prefers-reduced-motion: reduce)";

function subscribeToReducedMotion(onChange: () => void) {
  const media = window.matchMedia(reducedMotionQuery);
  media.addEventListener("change", onChange);
  return () => media.removeEventListener("change", onChange);
}

/** Background for the log in and register pages: three tilted rows of student photos and benefit cards that
 *  slide sideways forever (each row is drawn twice so the loop has no seam). It has a pause button, because
 *  moving backgrounds need one; people who ask for reduced motion see it still until they press play. */
export function PhotoRibbons() {
  const reducedMotion = useSyncExternalStore(
    subscribeToReducedMotion,
    () => window.matchMedia(reducedMotionQuery).matches,
    () => false,
  );
  // null until the visitor presses the button: until then it moves unless they asked for reduced motion.
  const [choice, setChoice] = useState<boolean | null>(null);
  const playing = choice ?? !reducedMotion;

  return (
    <>
      <div
        aria-hidden="true"
        data-paused={playing ? undefined : true}
        data-playing={choice === true ? true : undefined}
        className="photo-ribbons pointer-events-none absolute inset-x-[-10%] inset-y-[-60px] -z-10 flex -rotate-6 flex-col justify-around"
      >
        {rows.map((row, r) => (
          <div key={r} data-dir={row.direction} className={`ribbon-track flex w-max ${row.speed}`}>
            {[...row.tiles, ...row.tiles].map((tile, i) => (
              <RibbonTile key={i} tile={tile} />
            ))}
          </div>
        ))}
      </div>
      <button
        type="button"
        onClick={() => setChoice(!playing)}
        aria-label={playing ? "Pause background photos" : "Play background photos"}
        className="absolute bottom-4 right-4 z-10 grid size-11 place-items-center rounded-full bg-white/15 text-white ring-1 ring-white/25 backdrop-blur-md transition hover:bg-white/25 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-white/50 sm:bottom-6 sm:right-6"
      >
        {playing ? <Pause className="size-4" aria-hidden="true" /> : <Play className="size-4" aria-hidden="true" />}
      </button>
    </>
  );
}

const tileFrame = "relative mr-3.5 h-[128px] w-[180px] shrink-0 overflow-hidden rounded-[18px] sm:mr-[18px] sm:h-[176px] sm:w-[250px] sm:rounded-[20px]";

function RibbonTile({ tile }: { tile: Tile }) {
  if ("label" in tile) {
    return (
      <div
        className={`${tileFrame} flex items-end p-4 font-editorial text-[19px] font-semibold leading-[1.1] sm:p-5 sm:text-[26px] ${tile.tone}`}
      >
        {tile.label}
      </div>
    );
  }
  return (
    <div className={tileFrame}>
      <Image src={tile.src} alt="" fill sizes="(min-width: 640px) 250px, 180px" loading="eager" className={`object-cover ${tile.focus ?? ""}`} />
    </div>
  );
}
