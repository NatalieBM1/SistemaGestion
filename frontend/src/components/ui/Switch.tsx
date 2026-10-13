import { type InputHTMLAttributes, forwardRef } from "react";
import styles from "./Switch.module.css";

interface SwitchProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export const Switch = forwardRef<HTMLInputElement, SwitchProps>(
  ({ label, className, ...rest }, ref) => {
    return (
      <label className={[styles.wrapper, className].filter(Boolean).join(" ")}>
        <span className={styles.track}>
          <input ref={ref} type="checkbox" role="switch" className={styles.input} {...rest} />
          <span className={styles.thumb} aria-hidden="true" />
        </span>
        {label}
      </label>
    );
  },
);

Switch.displayName = "Switch";
