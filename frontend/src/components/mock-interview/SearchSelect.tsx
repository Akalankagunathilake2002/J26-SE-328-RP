"use client";

import { useId } from "react";
import Select, { type StylesConfig } from "react-select";

// Searchable dropdown (Select2-style: type to filter, keyboard navigation) in the site's ink-border style.
// Used for every dropdown in the mock interview and the Edu Assistant.

export interface SelectOption<V extends string | number = string> {
  value: V;
  label: string;
}

interface SearchSelectProps<V extends string | number> {
  inputId?: string;
  options: SelectOption<V>[];
  /** null shows the placeholder (e.g. a picker that resets after each choice) */
  value: V | null;
  onChange: (value: V) => void;
  placeholder?: string;
  disabled?: boolean;
  /** "sm" for compact toolbars */
  size?: "md" | "sm";
  ariaLabel?: string;
  className?: string;
}

export default function SearchSelect<V extends string | number>({
  inputId,
  options,
  value,
  onChange,
  placeholder = "Select…",
  disabled = false,
  size = "md",
  ariaLabel,
  className,
}: SearchSelectProps<V>) {
  // Stable ids keep server and client markup identical (react-select otherwise warns on hydration)
  const instanceId = useId();
  const small = size === "sm";
  const selected = value === null ? null : (options.find((o) => o.value === value) ?? null);

  const styles: StylesConfig<SelectOption<V>, false> = {
    control: (base, state) => ({
      ...base,
      minHeight: small ? 30 : 42,
      borderRadius: 0,
      border: `${small ? 1 : 2}px solid var(--color-ink)`,
      boxShadow: state.isFocused ? "3px 3px 0 var(--color-ink)" : "2px 2px 0 var(--color-ink)",
      backgroundColor: state.isDisabled ? "var(--color-cream)" : "white",
      cursor: "pointer",
      fontSize: small ? 12 : 14,
      fontWeight: small ? 500 : 700,
      "&:hover": { borderColor: "var(--color-ink)" },
    }),
    valueContainer: (base) => ({ ...base, padding: small ? "0 6px" : "2px 10px" }),
    singleValue: (base) => ({ ...base, color: "var(--color-ink)" }),
    placeholder: (base) => ({ ...base, color: "var(--color-muted)" }),
    input: (base) => ({ ...base, color: "var(--color-ink)" }),
    indicatorSeparator: () => ({ display: "none" }),
    dropdownIndicator: (base) => ({ ...base, color: "var(--color-ink)", padding: small ? 4 : 8 }),
    menu: (base) => ({
      ...base,
      borderRadius: 0,
      border: "2px solid var(--color-ink)",
      boxShadow: "4px 4px 0 var(--color-ink)",
      marginTop: 4,
      overflow: "hidden",
    }),
    menuList: (base) => ({ ...base, padding: 0 }),
    menuPortal: (base) => ({ ...base, zIndex: 60 }),
    option: (base, state) => ({
      ...base,
      cursor: "pointer",
      fontSize: small ? 12 : 14,
      fontWeight: state.isSelected ? 700 : 500,
      color: "var(--color-ink)",
      backgroundColor: state.isSelected ? "var(--color-lime)" : state.isFocused ? "var(--color-butter)" : "white",
      "&:active": { backgroundColor: "var(--color-lime)" },
    }),
    noOptionsMessage: (base) => ({ ...base, fontSize: 12, color: "var(--color-muted)" }),
  };

  return (
    <Select<SelectOption<V>, false>
      instanceId={instanceId}
      inputId={inputId}
      aria-label={ariaLabel}
      className={className}
      options={options}
      value={selected}
      onChange={(option) => option && onChange(option.value)}
      placeholder={placeholder}
      isDisabled={disabled}
      isSearchable
      noOptionsMessage={() => "No matches"}
      // Rendered on <body> so menus aren't clipped by panels with overflow hidden
      menuPortalTarget={typeof document === "undefined" ? undefined : document.body}
      menuPlacement="auto"
      styles={styles}
    />
  );
}
