import { useMutation } from "@tanstack/react-query";
import { Download, FileSpreadsheet } from "lucide-react";
import { useState } from "react";
import {
  descargarReporteFacturadas,
  descargarReporteGeneral,
  getBlobErrorMessage,
  guardarBlobComoArchivo,
  type ReporteFiltros,
} from "../../api/reportes";
import { AsyncSelect, Button, Input, PageHeader, useToast } from "../../components/ui";
import { usePageTitle } from "../../store/pageTitleStore";

function hoyISO(): string {
  return new Date().toISOString().slice(0, 10);
}

interface ReporteCardProps {
  titulo: string;
  descripcion: string;
  nombreArchivoBase: string;
  descargar: (filtros: ReporteFiltros) => Promise<Blob>;
}

function ReporteCard({ titulo, descripcion, nombreArchivoBase, descargar }: ReporteCardProps) {
  const toast = useToast();
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [clienteId, setClienteId] = useState<number | null>(null);
  const [proyectoId, setProyectoId] = useState<number | null>(null);
  const [vehiculoId, setVehiculoId] = useState<number | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      descargar({
        desde: desde || undefined,
        hasta: hasta || undefined,
        cliente_id: clienteId ?? undefined,
        proyecto_id: proyectoId ?? undefined,
        vehiculo_id: vehiculoId ?? undefined,
      }),
    onSuccess: (blob) => {
      guardarBlobComoArchivo(blob, `${nombreArchivoBase}-${hoyISO()}.xlsx`);
      toast.success("Reporte descargado correctamente.");
    },
    onError: async (error) => {
      toast.error(await getBlobErrorMessage(error, "No se pudo generar el reporte."));
    },
  });

  return (
    <div
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-md)",
        padding: "var(--space-5)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-1)" }}>
        <FileSpreadsheet size={20} strokeWidth={1.75} style={{ color: "var(--accent)" }} />
        <h3 style={{ margin: 0 }}>{titulo}</h3>
      </div>
      <p style={{ color: "var(--text-secondary)", margin: "0 0 var(--space-4)" }}>{descripcion}</p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "var(--space-3)", marginBottom: "var(--space-4)" }}>
        <Input label="Desde" type="date" value={desde} onChange={(e) => setDesde(e.target.value)} />
        <Input label="Hasta" type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} />
        <AsyncSelect
          label="Cliente (opcional)"
          endpoint="/api/terceros"
          params={{ tipo: "cliente" }}
          getLabel={(item) => String(item.nombre)}
          value={clienteId}
          onChange={setClienteId}
        />
        <AsyncSelect
          label="Proyecto (opcional)"
          endpoint="/api/catalogos/proyectos"
          getLabel={(item) => String(item.nombre)}
          value={proyectoId}
          onChange={setProyectoId}
        />
        <AsyncSelect
          label="Vehículo (opcional)"
          endpoint="/api/activos"
          params={{ tipo_activo: "Vehículo" }}
          getLabel={(item) => String(item.placa)}
          value={vehiculoId}
          onChange={setVehiculoId}
        />
      </div>

      <Button
        variant="primary"
        leftIcon={<Download size={16} />}
        loading={mutation.isPending}
        onClick={() => mutation.mutate()}
      >
        {mutation.isPending ? "Descargando…" : "Descargar Excel"}
      </Button>
    </div>
  );
}

export function Reportes() {
  usePageTitle("Reportes");

  return (
    <PageHeader
      title="Reportes"
      subtitle="Genera y descarga reportes en Excel del módulo de Remisiones, con filtros opcionales."
      breadcrumb={["Análisis", "Reportes"]}
    >
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "var(--space-5)" }}>
        <ReporteCard
          titulo="Reporte general de remisiones"
          descripcion="Todas las remisiones que coincidan con los filtros, con sus valores y estado de facturación."
          nombreArchivoBase="reporte-remisiones-general"
          descargar={descargarReporteGeneral}
        />
        <ReporteCard
          titulo="Reporte de remisiones facturadas"
          descripcion="Una fila por cada facturación activa (una remisión con varias facturaciones parciales aparece varias veces)."
          nombreArchivoBase="reporte-remisiones-facturadas"
          descargar={descargarReporteFacturadas}
        />
      </div>
    </PageHeader>
  );
}
