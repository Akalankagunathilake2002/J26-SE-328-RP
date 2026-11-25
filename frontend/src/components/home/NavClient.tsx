"use client";

import { useLinkStatus } from "next/link";
import { useEffect, useRef, type ReactNode } from "react";

/** Inside each header link. While that link's page is loading, the link already shows as selected (a soft
 *  pill with a gentle pulse), so a click gets feedback straight away. globals.css (.nav-links) turns the
 *  link purple and un-highlights the page you are leaving while this is showing. */
export function NavPendingPill() {
  const { pending } = useLinkStatus();
  return (
    <span
      aria-hidden="true"
      data-pending={pending ? "" : undefined}
      className={`pointer-events-none absolute inset-0 -z-10 rounded-full bg-[#efe8ff] transition-opacity duration-150 ${
        pending ? "animate-pulse opacity-100 motion-reduce:animate-none" : "opacity-0"
      }`}
    />
  );
}

/** The header's link row on phones and tablets. It scrolls sideways, so this keeps the selected link in
 *  view (for example Edu Assistant, which would otherwise sit off-screen on the right). */
export function MobileNav({ currentPath, className, children }: { currentPath: string; className: string; children: ReactNode }) {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const nav = ref.current;
    const current = nav?.querySelector<HTMLElement>('[aria-current="page"]');
    // offsetParent is null while the row is hidden (wide screens show the desktop links instead).
    if (!nav || !current || nav.offsetParent === null) return;
    const navBox = nav.getBoundingClientRect();
    const linkBox = current.getBoundingClientRect();
    nav.scrollLeft += linkBox.left - navBox.left - (navBox.width - linkBox.width) / 2;
  }, [currentPath]);

  return (
    <nav ref={ref} aria-label="Main" className={className}>
      {children}
    </nav>
  );
}
