"use client";

import { ChevronDown, Filter } from "lucide-react";
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
 * Role and industry filters. Choosing an industry narrows the role list to that industry's roles.
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
    <Form
      action="/market-pulse"
      scroll={false}
      className="border-2 border-ink bg-cream p-4 shadow-[5px_5px_0_var(--color-ink)]"
    >
      <p className="font-mono text-[14px] font-bold">Filter your job role</p>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        {/* An "all" choice has no name, so it is left out of the URL. */}
        <Select
          label="Job role"
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
        <Select
          label="Industry"
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
      </div>
      <button
        type="submit"
        className="mt-3 inline-flex h-10 w-full items-center justify-center gap-2 border-2 border-ink bg-lime text-[13px] font-bold uppercase tracking-[0.04em] shadow-[3px_3px_0_var(--color-ink)] transition-transform hover:-translate-y-0.5"
      >
        <Filter className="size-4" aria-hidden="true" />
        Apply filters
      </button>
    </Form>
  );
}

type SelectProps = {
  label: string;
  name: string | undefined;
  value: string;
  onChange: (value: string) => void;
  children: ReactNode;
};

function Select({ label, name, value, onChange, children }: SelectProps) {
  return (
    <label className="relative block">
      <span className="sr-only">{label}</span>
      <select
        name={name}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-10 w-full appearance-none truncate border-2 border-ink bg-white pl-3 pr-9 text-[14px] font-medium"
      >
        {children}
      </select>
      <ChevronDown aria-hidden="true" className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2" />
    </label>
  );
}
