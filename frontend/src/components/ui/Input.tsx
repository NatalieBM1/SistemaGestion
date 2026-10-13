import { type InputHTMLAttributes, type ReactNode, forwardRef, useId } from "react";
import styles from "./Input.module.css";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  monoData?: boolean;
  /** Ícono/botón flotante en el borde derecho del input (ej. mostrar/ocultar
   * contraseña). No desplaza el layout: se posiciona sobre el input. */
  rightElement?: ReactNode;
  /** Ícono decorativo a la izquierda del input (ej. Mail, Lock). */
  leftElement?: ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, monoData = false, rightElement, leftElement, id, className, required, ...rest }, ref) => {
    const generatedId = useId();
    const inputId = id ?? generatedId;

    return (
      <div className={styles.field}>
        {label && (
          <label className={styles.label} htmlFor={inputId}>
            {label}
            {required && (
              <span className={styles.required} aria-hidden="true">
                *
              </span>
            )}
          </label>
        )}
        <div className={styles.inputWrapper}>
          <input
            ref={ref}
            id={inputId}
            required={required}
            className={[
              styles.input,
              error ? styles.inputError : "",
              rightElement ? styles.hasRightElement : "",
              leftElement ? styles.hasLeftElement : "",
              monoData ? "font-mono-data" : "",
              className,
            ]
              .filter(Boolean)
              .join(" ")}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? `${inputId}-error` : undefined}
            {...rest}
          />
          {leftElement && <div className={styles.leftElement}>{leftElement}</div>}
          {rightElement && <div className={styles.rightElement}>{rightElement}</div>}
        </div>
        {error ? (
          <span id={`${inputId}-error`} className={styles.errorMessage} role="alert">
            {error}
          </span>
        ) : hint ? (
          <span className={styles.hint}>{hint}</span>
        ) : null}
      </div>
    );
  },
);

Input.displayName = "Input";
