"use client";

import { ChevronDown } from "lucide-react";
import Form from "next/form";
import { useState, type ReactNode } from "react";

type RoleOption = { role: string; sectors: string[]; ads: number };

type MarketPulseFiltersProps = {
  roles: RoleOption[];
  sectors: string[];
  role: string;
  sector: string;
  view: string; // kept in the URL, so applying filters stays on the same view
};

/**
 * Industry and role filters. Choosing an industry narrows the role list to that industry's roles.
 * Applying them updates the URL (?sector=…&role=…), and the page shows that selection.
 */
export function MarketPulseFilters({ roles, sectors, role, sector, view }: MarketPulseFiltersProps) {
  const [selectedRole, setSelectedRole] = useState(role);
  const [selectedSector, setSelectedSector] = useState(sector);
  const roleOptions = selectedSector ? roles.filter((r) => r.sectors.includes(selectedSector)) : roles;

  function chooseSector(value: string) {
    setSelectedSector(value);
    const current = roles.find((r) => r.role === selectedRole);
    if (value && current && !current.sectors.includes(value)) setSelectedRole("");
  }

  return (
    <Form action="/market-pulse" scroll={false} aria-label="Filter job ads" className="flex flex-wrap items-center gap-2">
      {view !== "overview" && <input type="hidden" name="view" value={view} />}
      {/* An "all" choice has no name, so it is left out of the URL. */}
      <Select label="Industry" name={selectedSector ? "sector" : undefined} value={selectedSector} onChange={chooseSector}>
        <option value="">All industries</option>
        {sectors.map((name) => (
          <option key={name} value={name}>
            {name}
          </option>
        ))}
      </Select>
      <Select label="Job role" name={selectedRole ? "role" : undefined} value={selectedRole} onChange={setSelectedRole} wide>
        <option value="">All roles</option>
        {roleOptions.map((option) => (
          <option key={option.role} value={option.role}>
            {option.role} ({option.ads})
          </option>
        ))}
      </Select>
      <button
        type="submit"
        className="h-10 rounded-lg bg-[#17161d] px-4 text-sm font-bold text-[#d0ffa4] transition-colors hover:bg-[#2b2935] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#17161d]"
      >
        Apply
      </button>
    </Form>
  );
}

type SelectProps = {
  label: string;
  name: string | undefined;
  value: string;
  onChange: (value: string) => void;
  wide?: boolean;
  children: ReactNode;
};

function Select({ label, name, value, onChange, wide = false, children }: SelectProps) {
  return (
    <label className={`relative block min-w-0 ${wide ? "w-full sm:w-60" : "w-full sm:w-44"}`}>
      <span className="sr-only">{label}</span>
      <select
        name={name}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-10 w-full cursor-pointer appearance-none truncate rounded-lg border border-[#dddce5] bg-white pl-3 pr-9 text-sm text-[#17161d] transition-colors hover:border-[#c4c2d0] focus:border-[#17161d] focus:outline-none focus:ring-2 focus:ring-[#17161d]/10"
      >
        {children}
      </select>
      <ChevronDown aria-hidden="true" className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-[#6b6979]" />
    </label>
  );
}
