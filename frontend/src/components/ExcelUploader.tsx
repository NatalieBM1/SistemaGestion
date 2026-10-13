import { useMutation } from "@tanstack/react-query";
import { FileSpreadsheet, Upload } from "lucide-react";
import { type DragEvent, type ReactNode, useRef, useState } from "react";
import type { CargaExcelResponse } from "../api/facturas";
import { getApiErrorMessage } from "../api/errors";
import { Badge, Button } from "./ui";
import styles from "./CatalogoCRUD.module.css";

interface ExcelUploaderProps {
  columnas: string[];
  instrucciones: ReactNode;
  onUpload: (file: File) => Promise<CargaExcelResponse>;
  disabled?: boolean;
  onSuccess?: () => void;
}

/** Drag-and-drop de un .xlsx (o click para seleccionar), reutilizado en las
 * 3 cargas masivas de Facturación. Sube el archivo al confirmar y muestra el
 * resumen de filas_totales/exitosas/error devuelto por el backend. */
export function ExcelUploader({ columnas, instrucciones, onUpload, disabled, onSuccess }: ExcelUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (archivo: File) => onUpload(archivo),
    onSuccess: () => {
      setError(null);
      onSuccess?.();
    },
    onError: (err) => setError(getApiErrorMessage(err, "No se pudo procesar el archivo.")),
  });

  const pickFile = (selected: File | null) => {
    setFile(selected);
    setError(null);
    mutation.reset();
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragOver(false);
    if (disabled) return;
    const dropped = event.dataTransfer.files?.[0];
    if (dropped) pickFile(dropped);
  };

  const resultado = mutation.data;

  return (
    <div>
      <div className={styles.confirmText} style={{ marginBottom: "var(--space-3)" }}>
        <strong>Columnas requeridas:</strong>{" "}
        <span className="font-mono-data">{columnas.join(", ")}</span>
        <div style={{ marginTop: "var(--space-2)" }}>{instrucciones}</div>
      </div>

      <div
        onDragOver={(event) => {
          event.preventDefault();
          if (!disabled) setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        style={{
          border: `2px dashed ${dragOver ? "var(--accent)" : "#c6d5fb"}`,
          borderRadius: "18px",
          padding: "var(--space-6)",
          textAlign: "center",
          cursor: disabled ? "not-allowed" : "pointer",
          background: dragOver
            ? "var(--accent-tint)"
            : "linear-gradient(180deg, #ffffff, #f2f6ff)",
          opacity: disabled ? 0.6 : 1,
          transition: "background-color var(--transition-fast), border-color var(--transition-fast)",
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".xlsx"
          hidden
          disabled={disabled}
          onChange={(event) => pickFile(event.target.files?.[0] ?? null)}
        />
        <FileSpreadsheet size={32} strokeWidth={1.5} style={{ color: "var(--text-secondary)" }} />
        <p style={{ margin: "var(--space-2) 0 0", color: "var(--text-secondary)" }}>
          {file ? (
            <>
              Archivo seleccionado: <strong>{file.name}</strong>
            </>
          ) : (
            "Arrastra un archivo .xlsx aquí, o haz clic para seleccionarlo."
          )}
        </p>
      </div>

      {error && (
        <div className={styles.formError} style={{ marginTop: "var(--space-3)" }}>
          {error}
        </div>
      )}

      <div style={{ marginTop: "var(--space-3)", display: "flex", justifyContent: "flex-end" }}>
        <Button
          variant="primary"
          leftIcon={<Upload size={16} />}
          disabled={!file || disabled}
          loading={mutation.isPending}
          onClick={() => file && mutation.mutate(file)}
        >
          {mutation.isPending ? "Procesando…" : "Procesar archivo"}
        </Button>
      </div>

      {resultado && (
        <div style={{ marginTop: "var(--space-5)" }}>
          <div style={{ display: "flex", gap: "var(--space-3)", flexWrap: "wrap", marginBottom: "var(--space-4)" }}>
            <Badge variant="neutral">Total: {resultado.filas_totales}</Badge>
            <Badge variant="success">Exitosas: {resultado.filas_exitosas}</Badge>
            <Badge variant={resultado.filas_error > 0 ? "danger" : "neutral"}>Con error: {resultado.filas_error}</Badge>
          </div>

          {resultado.filas_error > 0 && (
            <div>
              <p style={{ color: "var(--text-secondary)", marginBottom: "var(--space-2)" }}>
                Detalle de filas con error ({resultado.detalle_errores.length}):
              </p>
              <div style={{ maxHeight: 320, overflowY: "auto", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border)", background: "var(--bg-canvas)" }}>
                      {Object.keys(resultado.detalle_errores[0] ?? {}).map((key) => (
                        <th key={key} style={{ padding: "var(--space-2)", position: "sticky", top: 0, background: "var(--bg-canvas)" }}>
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {resultado.detalle_errores.map((fila, index) => (
                      <tr key={index} style={{ borderBottom: "1px solid var(--border)" }}>
                        {Object.keys(resultado.detalle_errores[0] ?? {}).map((key) => (
                          <td key={key} style={{ padding: "var(--space-2)" }}>
                            {String(fila[key] ?? "—")}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
