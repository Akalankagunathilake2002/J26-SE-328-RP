"use client";

import { useId } from "react";
import Select, { type StylesConfig } from "react-select";

// Searchable dropdown (Select2-style: type to filter, keyboard navigation) in the site's soft style.
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
      borderRadius: small ? 10 : 12,
      border: `1px solid ${state.isFocused ? "#6d4aff" : "#e4dfd5"}`,
      boxShadow: state.isFocused ? "0 0 0 4px rgb(109 74 255 / 0.15)" : "0 6px 14px -10px rgb(40 30 10 / 0.4)",
      backgroundColor: state.isDisabled ? "#f4f2ee" : "white",
      cursor: "pointer",
      fontSize: small ? 12 : 14,
      fontWeight: small ? 500 : 700,
      "&:hover": { borderColor: state.isFocused ? "#6d4aff" : "#c9bfff" },
    }),
    valueContainer: (base) => ({ ...base, padding: small ? "0 6px" : "2px 10px" }),
    singleValue: (base) => ({ ...base, color: "var(--color-ink)" }),
    placeholder: (base) => ({ ...base, color: "var(--color-muted)" }),
    input: (base) => ({ ...base, color: "var(--color-ink)" }),
    indicatorSeparator: () => ({ display: "none" }),
    dropdownIndicator: (base) => ({ ...base, color: "#8a877f", padding: small ? 4 : 8 }),
    menu: (base) => ({
      ...base,
      borderRadius: 14,
      border: "1px solid #e4dfd5",
      boxShadow: "0 18px 36px -20px rgb(40 30 10 / 0.5)",
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
      backgroundColor: state.isSelected ? "#efe8ff" : state.isFocused ? "#f6f3ff" : "white",
      "&:active": { backgroundColor: "#e4dcff" },
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
