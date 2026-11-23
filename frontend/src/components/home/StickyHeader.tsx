"use client";

import { useEffect, useState, type ReactNode } from "react";

/** Header that stays at the top while the page scrolls. Once the page has scrolled, it gets
 *  `data-scrolled`, which the soft header style uses to add a shadow. */
export function StickyHeader({ className, children }: { className: string; children: ReactNode }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const update = () => setScrolled(window.scrollY > 8);
    update();
    window.addEventListener("scroll", update, { passive: true });
    return () => window.removeEventListener("scroll", update);
  }, []);

  return (
    <header data-scrolled={scrolled || undefined} className={className}>
      {children}
    </header>
  );
}
