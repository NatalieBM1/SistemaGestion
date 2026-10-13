import { useQuery } from "@tanstack/react-query";
import { ChevronDown } from "lucide-react";
import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { apiClient } from "../../api/client";
import styles from "./AsyncSelect.module.css";

interface AsyncOption {
  id: number;
  label: string;
}

interface AsyncSelectProps {
  label?: string;
  endpoint: string;
  params?: Record<string, string | number | boolean | undefined>;
  getLabel: (item: Record<string, unknown>) => string;
  value: number | null | undefined;
  onChange: (id: number | null) => void;
  error?: string;
  required?: boolean;
  disabled?: boolean;
  placeholder?: string;
  hint?: string;
  icon?: ReactNode;
}

/** Combobox con búsqueda: un solo input de texto que, al escribir, filtra
 * opciones de un endpoint paginado de la API (mismo formato { items, total,
 * page, page_size } de catálogos) y las muestra en un dropdown superpuesto.
 * Si el valor actual no está en la página cargada (p.ej. al editar), se
 * resuelve aparte por id para no perder la etiqueta seleccionada. */
export function AsyncSelect({
  label,
  endpoint,
  params,
  getLabel,
  value,
  onChange,
  error,
  required,
  disabled,
  placeholder = "Buscar…",
  hint,
  icon,
}: AsyncSelectProps) {
  const generatedId = useId();
  const containerRef = useRef<HTMLDivElement>(null);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const timeout = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timeout);
  }, [search]);

  useEffect(() => {
    if (!isOpen) return;
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearch("");
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  const paramsKey = JSON.stringify(params ?? {});

  const { data, isLoading } = useQuery({
    queryKey: ["async-select", endpoint, paramsKey, debouncedSearch],
    queryFn: async () => {
      const { data } = await apiClient.get(endpoint, {
        params: { ...params, q: debouncedSearch || undefined, page: 1, page_size: 50 },
      });
      return data.items as Record<string, unknown>[];
    },
    enabled: isOpen,
  });

  const { data: selectedItem } = useQuery({
    queryKey: ["async-select-item", endpoint, value],
    queryFn: async () => {
      const { data } = await apiClient.get(`${endpoint}/${value}`);
      return data as Record<string, unknown>;
    },
    enabled: value != null,
  });

  const options: AsyncOption[] = (data ?? []).map((item) => ({
    id: item.id as number,
    label: getLabel(item),
  }));

  const selectedLabel = selectedItem ? getLabel(selectedItem) : null;

  const openDropdown = () => {
    if (disabled) return;
    setIsOpen(true);
    setSearch("");
  };

  const selectOption = (id: number | null) => {
    onChange(id);
    setIsOpen(false);
    setSearch("");
  };

  const displayValue = isOpen ? search : selectedLabel ?? "";

  return (
    <div className={styles.field} ref={containerRef}>
      {label && (
        <label className={styles.label} htmlFor={generatedId}>
          {label}
          {required && (
            <span className={styles.required} aria-hidden="true">
              *
            </span>
          )}
        </label>
      )}
      <div className={styles.control}>
        {icon && <span className={styles.leftIcon} aria-hidden="true">{icon}</span>}
        <input
          type="text"
          id={generatedId}
          role="combobox"
          aria-expanded={isOpen}
          aria-invalid={Boolean(error)}
          aria-required={required}
          autoComplete="off"
          className={[styles.input, icon ? styles.hasIcon : "", error ? styles.inputError : ""].filter(Boolean).join(" ")}
          placeholder={selectedLabel && !isOpen ? undefined : placeholder}
          value={displayValue}
          disabled={disabled}
          onFocus={openDropdown}
          onClick={openDropdown}
          onChange={(event) => {
            setSearch(event.target.value);
            setIsOpen(true);
          }}
          onKeyDown={(event) => {
            if (event.key === "Escape") {
              setIsOpen(false);
              setSearch("");
              event.currentTarget.blur();
            } else if (event.key === "Enter") {
              // Evita que Enter dispare el submit del formulario contenedor
              // mientras el dropdown está abierto.
              event.preventDefault();
              if (options.length > 0) selectOption(options[0].id);
            }
          }}
        />
        <ChevronDown size={16} className={styles.chevron} aria-hidden="true" />
        {isOpen && (
          <div className={styles.dropdown} role="listbox">
            {isLoading ? (
              <div className={styles.dropdownMessage}>Cargando…</div>
            ) : (
              <>
                {value != null && (
                  <button
                    type="button"
                    className={[styles.option, styles.optionClear].join(" ")}
                    onMouseDown={(event) => event.preventDefault()}
                    onClick={() => selectOption(null)}
                  >
                    — Ninguno —
                  </button>
                )}
                {options.length === 0 ? (
                  <div className={styles.dropdownMessage}>Sin resultados.</div>
                ) : (
                  options.map((option) => (
                    <button
                      key={option.id}
                      type="button"
                      role="option"
                      aria-selected={option.id === value}
                      className={[styles.option, option.id === value ? styles.optionActive : ""]
                        .filter(Boolean)
                        .join(" ")}
                      onMouseDown={(event) => event.preventDefault()}
                      onClick={() => selectOption(option.id)}
                    >
                      {option.label}
                    </button>
                  ))
                )}
              </>
            )}
          </div>
        )}
      </div>
      {error ? (
        <span className={styles.errorMessage} role="alert">
          {error}
        </span>
      ) : hint ? (
        <span className={styles.hint}>{hint}</span>
      ) : null}
    </div>
  );
}
