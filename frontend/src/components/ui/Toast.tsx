import { CheckCircle2, X, XCircle } from "lucide-react";
import { createPortal } from "react-dom";
import { create } from "zustand";
import styles from "./Toast.module.css";

type ToastVariant = "success" | "error";

interface ToastItem {
  id: string;
  message: string;
  variant: ToastVariant;
}

interface ToastState {
  toasts: ToastItem[];
  show: (message: string, variant: ToastVariant) => void;
  dismiss: (id: string) => void;
}

const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  show: (message, variant) => {
    const id = Math.random().toString(36).slice(2);
    set((state) => ({ toasts: [...state.toasts, { id, message, variant }] }));
    setTimeout(() => {
      set((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) }));
    }, 4000);
  },
  dismiss: (id) => set((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) })),
}));

export function useToast() {
  const show = useToastStore((state) => state.show);
  return {
    success: (message: string) => show(message, "success"),
    error: (message: string) => show(message, "error"),
  };
}

export function ToastContainer() {
  const toasts = useToastStore((state) => state.toasts);
  const dismiss = useToastStore((state) => state.dismiss);

  return createPortal(
    <div className={styles.container}>
      {toasts.map((toast) => (
        <div key={toast.id} className={[styles.toast, styles[toast.variant]].join(" ")} role="status">
          {toast.variant === "success" ? (
            <CheckCircle2 size={18} strokeWidth={2} />
          ) : (
            <XCircle size={18} strokeWidth={2} />
          )}
          <span>{toast.message}</span>
          <button
            type="button"
            className={styles.dismissButton}
            onClick={() => dismiss(toast.id)}
            aria-label="Descartar notificación"
          >
            <X size={14} />
          </button>
        </div>
      ))}
    </div>,
    document.body,
  );
}
