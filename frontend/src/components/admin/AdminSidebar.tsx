"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";
import {
  LayoutDashboard,
  Layers,
  Clock,
  ExternalLink,
  ShieldCheck,
} from "lucide-react";

interface AdminSidebarProps {
  pendingCount?: number;
}

const navItems = [
  {
    href: "/admin",
    label: "Dashboard",
    icon: LayoutDashboard,
    description: "Portal overview",
  },
  {
    href: "/admin/knowledge",
    label: "Shared Knowledge",
    icon: Layers,
    description: "Domains, roles, skills & graphs",
  },
  {
    href: "/admin/candidates",
    label: "Candidate Reviews",
    icon: Clock,
    description: "Entity & relationship proposals",
    showBadge: true,
  },
];

export function AdminSidebar({ pendingCount = 0 }: AdminSidebarProps) {
  const pathname = usePathname();

  return (
    <aside className="w-full shrink-0 border-b-[3px] border-ink bg-[#f5ecd8] md:min-h-screen md:w-64 md:border-b-0 md:border-r-[3px]">
      <div className="flex h-full flex-col justify-between">
        <div>
          {/* Brand & Admin Badge */}
          <div className="border-b-[3px] border-ink bg-white p-4">
            <div className="flex items-center justify-between">
              <Link href="/admin" className="flex items-center gap-2">
                <Image
                  src="/brand/skillaro-logo.png"
                  alt="Skillaro"
                  width={110}
                  height={38}
                  className="h-auto w-auto"
                  priority
                />
              </Link>
              <span className="hard-shadow-sm flex items-center gap-1 rounded bg-[#ffde4d] px-2 py-0.5 text-[11px] font-black uppercase tracking-wider text-ink">
                <ShieldCheck className="size-3.5" />
                Admin
              </span>
            </div>
            <p className="mt-1.5 text-[11px] font-semibold text-muted">
              SSKS Knowledge Administration
            </p>
          </div>

          {/* Navigation Links */}
          <nav className="p-3">
            <p className="px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-muted">
              Management
            </p>
            <ul className="space-y-1.5">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive =
                  item.href === "/admin"
                    ? pathname === "/admin"
                    : pathname.startsWith(item.href);

                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={`flex items-center justify-between rounded-lg border-2 px-3 py-2.5 text-sm font-semibold transition-all ${
                        isActive
                          ? "hard-shadow-sm border-ink bg-[#d0ffa4] text-ink"
                          : "border-transparent text-ink hover:border-ink hover:bg-white"
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <Icon className="size-4 shrink-0" />
                        <span>{item.label}</span>
                      </div>
                      {item.showBadge && pendingCount > 0 && (
                        <span className="hard-shadow-sm rounded-full bg-[#eba0ff] px-2 py-0.5 text-[11px] font-extrabold text-ink">
                          {pendingCount}
                        </span>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>
        </div>

        {/* Footer info & public portal link */}
        <div className="border-t-[3px] border-ink bg-white p-3">
          <div className="mb-3 rounded border-2 border-ink bg-[#fff9f2] p-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-bold text-ink">SSKS Service</span>
              <span className="flex items-center gap-1 text-[11px] font-bold text-green-700">
                <span className="inline-block size-2 rounded-full bg-green-500 animate-pulse" />
                Active
              </span>
            </div>
            <p className="mt-0.5 text-[11px] text-muted">Shared Skill Knowledge v1.0</p>
          </div>

          <Link
            href="/"
            className="hard-shadow-sm flex w-full items-center justify-center gap-2 rounded border-2 border-ink bg-page px-3 py-2 text-xs font-bold text-ink transition-transform hover:-translate-y-0.5"
          >
            <ExternalLink className="size-3.5" />
            Exit to Skillaro App
          </Link>
        </div>
      </div>
    </aside>
  );
}
