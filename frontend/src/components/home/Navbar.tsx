import Image from "next/image";
import Link from "next/link";

import { logout } from "@/app/actions/auth";
import { getCurrentUser } from "@/lib/auth";

import { navLinks } from "./links";
import { MobileNav, NavPendingPill } from "./NavClient";
import { StickyHeader } from "./StickyHeader";

/** "soft" (the default on every page) is a floating rounded bar that stays at the top while the page
 *  scrolls; the current page's link is a purple pill. "classic" is the original neo-brutal look, kept in
 *  case a page needs it. Only the styling differs: the links, layout and behaviour are the same. */
const looks = {
  classic: {
    header: "relative z-20 bg-white border-b-[3px] border-ink",
    panel: "",
    logo: "",
    avatar: "border-2 border-ink bg-[#ffe03a]",
    admin: "hard-shadow-sm rounded bg-lime text-ink",
    login: "h-10 hard-shadow-sm bg-lime hover:-translate-y-0.5",
    mobileNav: "border-t-2 border-ink py-2",
    list: "gap-[26px] text-[15.5px]",
    link: "underline-offset-4 hover:underline",
  },
  soft: {
    // The header itself is a transparent strip; the rounded panel inside it floats 12 px from the top
    // and gets a shadow once the page has scrolled (StickyHeader sets data-scrolled).
    header: "group sticky top-3 z-30 mt-3 px-3 sm:px-5",
    panel:
      "mx-auto max-w-[1400px] rounded-[22px] border border-[#e4e1da] bg-[#fafafa] shadow-[0_1px_2px_rgba(40,30,10,0.06)] transition-shadow duration-200 group-data-[scrolled]:shadow-[0_14px_36px_-16px_rgba(40,30,10,0.35)]",
    // The logo image has a white background; multiply makes it blend into the light grey panel.
    logo: "mix-blend-multiply",
    avatar: "bg-[#efe8ff] text-[#4a2fd0]",
    admin: "rounded-full bg-[#d5f5e3] text-[#145a36]",
    login:
      "h-11 rounded-[14px] bg-[#5b3df5] text-white shadow-[0_10px_22px_-12px_rgba(91,61,245,0.9)] hover:bg-[#4a2fd0] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#5b3df5]/30",
    // Each link is a pill (the current page's is purple). The pill padding plus the smaller gap add up to
    // the old spacing (28 px, 40 px from xl), and the list's negative margin keeps the text where it was,
    // so the header is no wider or taller than before. py-0.5 on the phone row offsets the pill's height.
    mobileNav: "border-t border-[#ebe8e1] py-0.5",
    list: "-mx-3 gap-1 text-[15.5px] xl:-mx-4 xl:gap-2 xl:text-[16.5px]",
    link: "relative isolate inline-flex items-center rounded-full px-3 py-1.5 text-[#6b6979] transition-colors hover:bg-[#f1eee8] hover:text-[#141413] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#6d4aff]/25 aria-[current=page]:bg-[#efe8ff] aria-[current=page]:text-[#4a2fd0] xl:px-4",
  },
};

export async function Navbar({
  currentPath = "/",
  variant = "soft",
}: {
  currentPath?: string;
  variant?: keyof typeof looks;
}) {
  const user = await getCurrentUser();
  const look = looks[variant];
  const Shell = variant === "soft" ? StickyHeader : "header";

  return (
    <Shell className={`font-nav ${look.header}`}>
      <div className={look.panel}>
        <div className="mx-auto grid h-[61px] max-w-[1440px] grid-cols-[1fr_auto] items-center gap-6 px-4 lg:grid-cols-[1fr_auto_1fr] lg:px-7">
          <Link href="/" aria-label="Skillaro home" className="justify-self-start">
            <Image
              src="/brand/skillaro-logo.png"
              alt="Skillaro — Align your skills. Shape your career"
              width={141}
              height={48}
              loading="eager"
              className={look.logo}
            />
          </Link>

          <nav aria-label="Main" className="hidden lg:block">
            <NavList currentPath={currentPath} listClass={look.list} linkClass={look.link} />
          </nav>

          <div className="justify-self-end">
            {user ? (
              <div className="flex items-center gap-3 text-[16px] font-medium">
                <span
                  aria-hidden="true"
                  className={`grid size-8 place-items-center rounded-full text-[14px] font-bold ${look.avatar}`}
                >
                  {user.full_name.charAt(0).toUpperCase()}
                </span>
                <span className="hidden sm:inline">{user.full_name}</span>
                {user.role === "admin" && (
                  <Link
                    href="/admin"
                    className={`px-2 py-0.5 text-[12px] font-bold uppercase tracking-wider ${look.admin}`}
                  >
                    Admin
                  </Link>
                )}
                <form action={logout}>
                  <button type="submit" className="ml-2 text-[15px] underline underline-offset-4 hover:text-brand-blue">
                    Log out
                  </button>
                </form>
              </div>
            ) : (
              <Link
                href="/login"
                className={`inline-flex items-center px-6 text-[16px] font-semibold transition ${look.login}`}
              >
                Login
              </Link>
            )}
          </div>
        </div>

        {/* The list is as wide as its links (w-max), so the row's end padding (pr-7, which also covers the
            list's negative margin) leaves space after the last link when scrolled all the way. */}
        <MobileNav currentPath={currentPath} className={`overflow-x-auto pl-4 pr-7 lg:hidden ${look.mobileNav}`}>
          <NavList currentPath={currentPath} listClass={`w-max ${look.list}`} linkClass={look.link} />
        </MobileNav>
      </div>
    </Shell>
  );
}

function NavList({ currentPath, listClass, linkClass }: { currentPath: string; listClass: string; linkClass: string }) {
  return (
    <ul className={`nav-links flex items-center whitespace-nowrap font-medium ${listClass}`}>
      {navLinks.map((link) => (
        <li key={link.href}>
          <Link
            href={link.href}
            className={linkClass}
            aria-current={link.href === currentPath ? "page" : undefined}
          >
            <NavPendingPill />
            {link.label}
          </Link>
        </li>
      ))}
    </ul>
  );
}
