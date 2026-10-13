import { Inbox } from "lucide-react";
import type { ReactNode } from "react";
import styles from "./EmptyState.module.css";

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
  icon?: ReactNode;
}

export function EmptyState({ title, description, action, icon }: EmptyStateProps) {
  return (
    <div className={styles.wrapper}>
      <div className={styles.icon}>{icon ?? <Inbox size={32} strokeWidth={1.5} />}</div>
      <div className={styles.title}>{title}</div>
      {description && <div className={styles.description}>{description}</div>}
      {action}
    </div>
  );
}
