"use client";

import { logout } from "@/app/actions/auth";
import { LogOut, ChevronDown } from "lucide-react";

interface AdminHeaderProps {
  user: {
    full_name: string;
    email: string;
    role?: string;
  };
  title?: string;
  subtitle?: string;
}

export function AdminHeader({
  user,
  title = "Admin Portal",
  subtitle = "Skillaro Shared Skill Knowledge Service",
}: AdminHeaderProps) {
  const initial = user.full_name ? user.full_name.charAt(0).toUpperCase() : "A";

  return (
    <header className="border-b-2 border-ink bg-[#FAF8F5] px-6 py-2.5 sm:py-3">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-black tracking-tight text-ink sm:text-2xl">
            {title}
          </h1>
          <p className="mt-0.5 text-xs font-medium text-[#5F5F5F]">
            {subtitle}
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-3">
          <div className="flex h-11 items-center gap-2.5 rounded-xl border-2 border-ink bg-white px-3 shadow-[2px_2px_0px_#0d0d0d]">
            <span
              aria-hidden="true"
              className="grid size-7 shrink-0 place-items-center rounded-full border-2 border-ink bg-[#FFE66D] text-xs font-black text-ink"
            >
              {initial}
            </span>
            <div className="flex flex-col text-left">
              <span className="text-xs font-black leading-tight text-ink">
                {user.full_name || "Admin"}
              </span>
              <span className="text-[10px] font-black uppercase tracking-wider text-emerald-700 leading-tight">
                ADMIN
              </span>
            </div>
            <ChevronDown className="ml-0.5 size-3.5 shrink-0 text-ink" />
          </div>

          <form action={logout} className="flex">
            <button
              type="submit"
              className="flex h-11 items-center gap-2 rounded-xl border-2 border-ink bg-[#FED7E2] px-3.5 text-xs font-black text-ink shadow-[2px_2px_0px_#0d0d0d] transition-transform hover:-translate-y-0.5 active:translate-y-0"
              title="Sign out of admin session"
            >
              <LogOut className="size-4 shrink-0 text-ink" />
              <span>Log out</span>
            </button>
          </form>
        </div>
      </div>
    </header>
  );
}
