import { type ButtonHTMLAttributes, type ReactNode, forwardRef } from "react";
import styles from "./Button.module.css";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
  loading?: boolean;
  leftIcon?: ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "secondary",
      size = "md",
      fullWidth = false,
      loading = false,
      leftIcon,
      disabled,
      children,
      className,
      ...rest
    },
    ref,
  ) => {
    const classes = [
      styles.button,
      styles[variant],
      styles[size],
      fullWidth ? styles.fullWidth : "",
      className,
    ]
      .filter(Boolean)
      .join(" ");

    return (
      <button ref={ref} className={classes} disabled={disabled || loading} {...rest}>
        {loading ? <span className={styles.spinner} aria-hidden="true" /> : leftIcon}
        {children}
      </button>
    );
  },
);

Button.displayName = "Button";
