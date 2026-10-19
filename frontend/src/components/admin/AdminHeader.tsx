"use client";

import { logout } from "@/app/actions/auth";
import { LogOut } from "lucide-react";

interface AdminHeaderProps {
  user: {
    full_name: string;
    email: string;
    role?: string;
  };
  title?: string;
  subtitle?: string;
}

export function AdminHeader({ user, title = "Admin Portal", subtitle = "Skillaro Shared Skill Knowledge Service" }: AdminHeaderProps) {
  return (
    <header className="border-b-[3px] border-ink bg-white px-4 py-3.5 sm:px-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-black tracking-tight text-ink sm:text-2xl">
            {title}
          </h1>
          <p className="text-xs font-medium text-muted sm:text-sm">
            {subtitle}
          </p>
        </div>

        <div className="flex items-center gap-3 self-end sm:self-auto">
          <div className="hard-shadow-sm flex items-center gap-2 rounded-lg border-2 border-ink bg-[#fff9f2] px-3 py-1.5">
            <span
              aria-hidden="true"
              className="grid size-7 place-items-center rounded-full border-2 border-ink bg-[#ffe03a] text-xs font-black"
            >
              {user.full_name.charAt(0).toUpperCase()}
            </span>
            <div className="text-left">
              <p className="text-xs font-bold leading-tight text-ink sm:text-sm">
                {user.full_name}
              </p>
              <span className="inline-block text-[10px] font-bold uppercase tracking-wider text-green-700">
                {user.role || "Admin"}
              </span>
            </div>
          </div>

          <form action={logout}>
            <button
              type="submit"
              className="hard-shadow-sm flex items-center gap-1.5 rounded-lg border-2 border-ink bg-[#ffefdc] px-3 py-2 text-xs font-bold text-ink transition-all hover:bg-[#ffe66d] hover:-translate-y-0.5 active:translate-y-0"
              title="Sign out of admin session"
            >
              <LogOut className="size-3.5" />
              <span className="hidden sm:inline">Log out</span>
            </button>
          </form>
        </div>
      </div>
    </header>
  );
}
