import type { ButtonHTMLAttributes, ReactNode } from "react";
import styles from "./IconButton.module.css";

type IconButtonVariant = "default" | "accent" | "danger";

interface IconButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children"> {
  label: string;
  icon: ReactNode;
  variant?: IconButtonVariant;
}

export function IconButton({ label, icon, variant = "default", className, type = "button", ...rest }: IconButtonProps) {
  const classes = [styles.button, styles[variant], className].filter(Boolean).join(" ");
  return (
    <button type={type} className={classes} title={label} aria-label={label} {...rest}>
      {icon}
    </button>
  );
}
