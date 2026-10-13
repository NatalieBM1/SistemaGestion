import { X } from "lucide-react";
import { type ReactNode, useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";
import styles from "./Modal.module.css";

type ModalSize = "sm" | "md" | "lg";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  /** Botones de acción (Cancelar/Guardar). Si se omite, el modal no muestra
   * footer — varios formularios ya traen sus propios botones en el body. */
  footer?: ReactNode;
  /** sm=420px, md=560px (default), lg=800px. */
  size?: ModalSize;
  children: ReactNode;
}

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function Modal({ open, onClose, title, footer, size = "md", children }: ModalProps) {
  const contentRef = useRef<HTMLDivElement>(null);
  const titleId = useId();
  const triggerRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!open) return;

    triggerRef.current = document.activeElement as HTMLElement | null;
    const content = contentRef.current;
    const focusable = content?.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
    (focusable?.[0] ?? content)?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
        return;
      }
      if (event.key !== "Tab" || !content) return;

      const nodes = content.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
      if (nodes.length === 0) return;
      const first = nodes[0];
      const last = nodes[nodes.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      triggerRef.current?.focus();
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div
      className={styles.overlay}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        className={[styles.content, styles[size]].join(" ")}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? titleId : undefined}
        ref={contentRef}
        tabIndex={-1}
      >
        {title && (
          <div className={styles.header}>
            <span id={titleId} className={styles.title}>
              {title}
            </span>
            <button type="button" className={styles.closeButton} onClick={onClose} aria-label="Cerrar">
              <X size={18} />
            </button>
          </div>
        )}
        <div className={styles.body}>{children}</div>
        {footer && <div className={styles.footer}>{footer}</div>}
      </div>
    </div>,
    document.body,
  );
}
