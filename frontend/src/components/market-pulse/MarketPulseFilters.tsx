"use client";

import { Briefcase, ChevronDown, Filter, Monitor, type LucideIcon } from "lucide-react";
import Form from "next/form";
import { useState, type ReactNode } from "react";

type RoleOption = { role: string; sectors: string[]; ads: number };

type MarketPulseFiltersProps = {
  roles: RoleOption[];
  sectors: string[];
  role: string;
  sector: string;
};

/**
 * Industry and role filters. Choosing an industry narrows the role list to that industry's roles.
 * Applying them updates the URL (?role=…&sector=…), and the page shows that selection.
 */
export function MarketPulseFilters({ roles, sectors, role, sector }: MarketPulseFiltersProps) {
  const [selectedRole, setSelectedRole] = useState(role);
  const [selectedSector, setSelectedSector] = useState(sector);
  const roleOptions = selectedSector ? roles.filter((r) => r.sectors.includes(selectedSector)) : roles;

  function chooseSector(value: string) {
    setSelectedSector(value);
    const current = roles.find((r) => r.role === selectedRole);
    if (value && current && !current.sectors.includes(value)) setSelectedRole("");
  }

  return (
    <Form action="/market-pulse" scroll={false}>
      <div className="grid gap-4 sm:grid-cols-2">
        {/* An "all" choice has no name, so it is left out of the URL. */}
        <Select
          label="Industry"
          Icon={Monitor}
          name={selectedSector ? "sector" : undefined}
          value={selectedSector}
          onChange={chooseSector}
        >
          <option value="">All industries</option>
          {sectors.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </Select>
        <Select
          label="Job role"
          Icon={Briefcase}
          name={selectedRole ? "role" : undefined}
          value={selectedRole}
          onChange={setSelectedRole}
        >
          <option value="">All roles</option>
          {roleOptions.map((option) => (
            <option key={option.role} value={option.role}>
              {option.role} ({option.ads})
            </option>
          ))}
        </Select>
      </div>
      <button
        type="submit"
        className="mt-4 flex w-full items-center justify-center gap-2.5 rounded-xl border-2 border-ink bg-sun px-6 py-3.5 text-base font-black text-ink shadow-[3px_3px_0px_#000] transition-all hover:-translate-y-0.5 hover:bg-butter sm:text-lg"
      >
        <Filter className="size-5" aria-hidden="true" />
        Apply filters
      </button>
    </Form>
  );
}

type SelectProps = {
  label: string;
  Icon: LucideIcon;
  name: string | undefined;
  value: string;
  onChange: (value: string) => void;
  children: ReactNode;
};

function Select({ label, Icon, name, value, onChange, children }: SelectProps) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-ink">{label}</span>
      <span className="relative block">
        <Icon aria-hidden="true" className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-ink/70" />
        <select
          name={name}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="w-full cursor-pointer appearance-none truncate rounded-xl border-2 border-ink bg-white py-3 pl-11 pr-10 text-sm font-semibold text-ink shadow-[2px_2px_0px_#000] transition-colors hover:bg-cream"
        >
          {children}
        </select>
        <ChevronDown aria-hidden="true" className="pointer-events-none absolute right-4 top-1/2 size-4 -translate-y-1/2" />
      </span>
    </label>
  );
}
