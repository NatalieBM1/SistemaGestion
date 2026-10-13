import { useQueryClient } from "@tanstack/react-query";
import { Trash2, Upload, UploadCloud } from "lucide-react";
import { useState } from "react";
import { actualizarPorExcel, eliminarPorExcel, facturarMasivoExcel } from "../../api/facturas";
import { PageHeader, TabsBar, type TabItem } from "../../components/ui";
import { ExcelUploader } from "../../components/ExcelUploader";
import { canWrite } from "../../lib/permissions";
import { useAuthStore } from "../../store/authStore";
import { usePageTitle } from "../../store/pageTitleStore";
import styles from "../../components/CatalogoCRUD.module.css";

type Tab = "facturar" | "eliminar" | "actualizar";

const TABS: TabItem<Tab>[] = [
  { key: "facturar", label: "Facturar masivo", icon: <UploadCloud size={16} /> },
  { key: "eliminar", label: "Eliminar por Excel", icon: <Trash2 size={16} /> },
  { key: "actualizar", label: "Actualizar por Excel", icon: <Upload size={16} /> },
];

export function CargasExcel() {
  usePageTitle("Cargas por Excel");
  const user = useAuthStore((state) => state.user);
  const puedeEscribir = canWrite(user);
  const [tab, setTab] = useState<Tab>("facturar");
  const queryClient = useQueryClient();

  const invalidarListados = () => {
    queryClient.invalidateQueries({ queryKey: ["facturas"] });
    queryClient.invalidateQueries({ queryKey: ["remisiones"] });
  };

  return (
    <PageHeader
      title="Cargas por Excel"
      breadcrumb={["Operación", { label: "Volver a facturas", to: "/facturas" }]}
    >
      <TabsBar items={TABS} value={tab} onChange={setTab} />

      {!puedeEscribir && (
        <div className={styles.formError} style={{ marginBottom: "var(--space-4)" }}>
          Tu rol (Solo Consulta) no tiene permiso para procesar cargas. Puedes ver las instrucciones, pero el botón
          está deshabilitado.
        </div>
      )}

      {tab === "facturar" && (
        <ExcelUploader
          columnas={["ID", "ES_PARCIAL", "VALOR_PARCIAL", "NUMERO_FACTURA", "FECHA_FACTURA"]}
          instrucciones={
            <ul style={{ margin: 0, paddingLeft: "var(--space-5)" }}>
              <li>ID: id de la remisión a facturar.</li>
              <li>ES_PARCIAL: "S" o "N". Si es "N", factura el saldo total pendiente.</li>
              <li>VALOR_PARCIAL: obligatorio solo cuando ES_PARCIAL="S".</li>
              <li>NUMERO_FACTURA: formato "F-1234" (una letra mayúscula, guion y dígitos).</li>
              <li>FECHA_FACTURA: formato dd/mm/aaaa.</li>
            </ul>
          }
          onUpload={facturarMasivoExcel}
          disabled={!puedeEscribir}
          onSuccess={invalidarListados}
        />
      )}

      {tab === "eliminar" && (
        <ExcelUploader
          columnas={["ID"]}
          instrucciones={
            <p style={{ margin: 0 }}>
              ID: id de la remisión cuyas facturaciones activas se anularán. El saldo de la remisión se recalcula
              automáticamente.
            </p>
          }
          onUpload={eliminarPorExcel}
          disabled={!puedeEscribir}
          onSuccess={invalidarListados}
        />
      )}

      {tab === "actualizar" && (
        <ExcelUploader
          columnas={["NUMERO_FACTURA_ACTUAL", "NUMERO_FACTURA_NUEVO", "FECHA_FACTURA_NUEVA"]}
          instrucciones={
            <ul style={{ margin: 0, paddingLeft: "var(--space-5)" }}>
              <li>NUMERO_FACTURA_ACTUAL: número de la factura existente a modificar.</li>
              <li>NUMERO_FACTURA_NUEVO: opcional, déjalo vacío para no cambiar el número.</li>
              <li>FECHA_FACTURA_NUEVA: opcional (formato dd/mm/aaaa), déjalo vacío para no cambiar la fecha.</li>
            </ul>
          }
          onUpload={actualizarPorExcel}
          disabled={!puedeEscribir}
          onSuccess={invalidarListados}
        />
      )}
    </PageHeader>
  );
}
