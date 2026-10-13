import type { ReactNode } from "react";
import styles from "./TabsBar.module.css";

export interface TabItem<K extends string> {
  key: K;
  label: string;
  icon?: ReactNode;
  count?: number;
  disabled?: boolean;
  disabledHint?: string;
}

interface TabsBarProps<K extends string> {
  items: TabItem<K>[];
  value: K;
  onChange: (key: K) => void;
}

export function TabsBar<K extends string>({ items, value, onChange }: TabsBarProps<K>) {
  return (
    <div className={styles.tabs} role="tablist">
      {items.map((item) => {
        const active = item.key === value;
        return (
          <button
            key={item.key}
            type="button"
            role="tab"
            aria-selected={active}
            disabled={item.disabled}
            title={item.disabled ? item.disabledHint : undefined}
            className={[styles.tab, active ? styles.tabActive : ""].filter(Boolean).join(" ")}
            onClick={() => onChange(item.key)}
          >
            {item.icon}
            {item.label}
            {item.count !== undefined && <b className={styles.count}>{item.count}</b>}
          </button>
        );
      })}
    </div>
  );
}
