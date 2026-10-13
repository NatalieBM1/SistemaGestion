import { Check } from "lucide-react";
import { type InputHTMLAttributes, forwardRef } from "react";
import styles from "./Checkbox.module.css";

interface CheckboxProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, className, ...rest }, ref) => {
    return (
      <label className={[styles.wrapper, className].filter(Boolean).join(" ")}>
        <span className={styles.inputWrap}>
          <input ref={ref} type="checkbox" className={styles.input} {...rest} />
          <span className={styles.box} aria-hidden="true">
            <Check size={13} strokeWidth={3} />
          </span>
        </span>
        {label}
      </label>
    );
  },
);

Checkbox.displayName = "Checkbox";
