import Image from "next/image";
import Link from "next/link";

import { logout } from "@/app/actions/auth";
import { getCurrentUser } from "@/lib/auth";

import { navLinks } from "./links";

export async function Navbar({ currentPath = "/" }: { currentPath?: string }) {
  const user = await getCurrentUser();

  return (
    <header className="relative z-20 border-b-[3px] border-ink bg-white font-nav">
      <div className="mx-auto grid h-[61px] max-w-[1440px] grid-cols-[1fr_auto] items-center gap-6 px-4 lg:grid-cols-[1fr_auto_1fr] lg:px-7">
        <Link href="/" aria-label="Skillaro home" className="justify-self-start">
          <Image
            src="/brand/skillaro-logo.png"
            alt="Skillaro — Align your skills. Shape your career"
            width={141}
            height={48}
            loading="eager"
          />
        </Link>

        <nav aria-label="Main" className="hidden lg:block">
          <NavList currentPath={currentPath} />
        </nav>

        <div className="justify-self-end">
          {user ? (
            <div className="flex items-center gap-3 text-[16px] font-medium">
              <span
                aria-hidden="true"
                className="grid size-8 place-items-center rounded-full border-2 border-ink bg-[#ffe03a] text-[14px] font-bold"
              >
                {user.full_name.charAt(0).toUpperCase()}
              </span>
              <span className="hidden sm:inline">{user.full_name}</span>
              <form action={logout}>
                <button type="submit" className="ml-2 text-[15px] underline underline-offset-4 hover:text-brand-blue">
                  Log out
                </button>
              </form>
            </div>
          ) : (
            <Link
              href="/login"
              className="hard-shadow-sm inline-flex h-10 items-center bg-lime px-6 text-[16px] font-semibold transition-transform hover:-translate-y-0.5"
            >
              Login
            </Link>
          )}
        </div>
      </div>

      <nav aria-label="Main" className="overflow-x-auto border-t-2 border-ink px-4 py-2 lg:hidden">
        <NavList currentPath={currentPath} />
      </nav>
    </header>
  );
}

function NavList({ currentPath }: { currentPath: string }) {
  return (
    <ul className="flex items-center gap-[26px] whitespace-nowrap text-[15.5px] font-medium">
      {navLinks.map((link) => (
        <li key={link.href}>
          <Link
            href={link.href}
            className="underline-offset-4 hover:underline"
            aria-current={link.href === currentPath ? "page" : undefined}
          >
            {link.label}
          </Link>
        </li>
      ))}
    </ul>
  );
}
