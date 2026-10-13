import { type ReactNode, type SelectHTMLAttributes, forwardRef, useId } from "react";
import styles from "./Input.module.css";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  hint?: string;
  children: ReactNode;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, hint, id, className, children, ...rest }, ref) => {
    const generatedId = useId();
    const selectId = id ?? generatedId;

    return (
      <div className={styles.field}>
        {label && (
          <label className={styles.label} htmlFor={selectId}>
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={selectId}
          className={[styles.input, error ? styles.inputError : "", className].filter(Boolean).join(" ")}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${selectId}-error` : undefined}
          {...rest}
        >
          {children}
        </select>
        {error ? (
          <span id={`${selectId}-error`} className={styles.errorMessage} role="alert">
            {error}
          </span>
        ) : hint ? (
          <span className={styles.hint}>{hint}</span>
        ) : null}
      </div>
    );
  },
);

Select.displayName = "Select";
