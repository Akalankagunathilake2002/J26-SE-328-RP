"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";
import {
  LayoutDashboard,
  Layers,
  Clock,
  ExternalLink,
  Box,
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
    <aside className="w-full shrink-0 border-b-2 border-ink bg-[#FAF8F5] md:h-full md:w-64 md:border-b-0 md:border-r-2">
      <div className="flex h-full flex-col justify-between">
        <div>
          {/* Brand header */}
          <div className="p-5 pb-1">
            <Link href="/admin" className="inline-block">
              <Image
                src="/brand/skillaro-logo.png"
                alt="Skillaro"
                width={120}
                height={38}
                className="h-7 w-auto"
                priority
              />
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="px-3.5 py-1">
            <p className="px-2 pt-3 pb-1.5 text-[11px] font-extrabold uppercase tracking-widest text-[#71717A]">
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
                      className={`flex items-center justify-between rounded-xl border-2 px-3 py-2 text-sm transition-all ${isActive
                          ? "border-ink bg-[#FFE66D] font-black text-ink shadow-[3px_3px_0px_#0d0d0d]"
                          : "border-transparent font-bold text-ink hover:border-ink hover:bg-white"
                        }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <Icon className="size-4.5 shrink-0 text-ink" />
                        <span>{item.label}</span>
                      </div>
                      {item.showBadge && pendingCount > 0 && (
                        <span className="flex size-5.5 shrink-0 items-center justify-center rounded-full border-2 border-ink bg-[#FFB4D6] text-[11px] font-black text-ink">
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
        <div className="mt-auto space-y-2.5 p-3.5 sm:p-4">
          <div className="rounded-xl border-2 border-ink bg-white p-3 shadow-[3px_3px_0px_#0d0d0d]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Box className="size-4 text-ink" />
                <span className="text-xs font-black text-ink">SSKS Service</span>
              </div>
              <span className="flex items-center gap-1.5 text-xs font-black text-emerald-700">
                <span className="size-2 rounded-full bg-emerald-500 animate-pulse" />
                Active
              </span>
            </div>
            <p className="mt-0.5 text-[11px] font-medium text-[#5F5F5F]">
              Shared Skill Knowledge v1.0
            </p>
          </div>

          <Link
            href="/"
            className="flex w-full items-center gap-2 rounded-xl border-2 border-ink bg-[#E9D5FF] px-3.5 py-2 text-xs font-black text-ink shadow-[3px_3px_0px_#0d0d0d] transition-transform hover:-translate-y-0.5 hover:shadow-[4px_4px_0px_#0d0d0d] active:translate-y-0"
          >
            <ExternalLink className="size-4 shrink-0 text-ink" />
            <span>Exit to Skillaro App</span>
          </Link>
        </div>
      </div>
    </aside>
  );
}
