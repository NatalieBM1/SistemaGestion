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
import { AsyncSelect, Badge, Button, Input, PageHeader, Select, useToast } from "../../components/ui";
import { usePageTitle } from "../../store/pageTitleStore";
import styles from "./Reportes.module.css";

function hoyISO(): string {
  return new Date().toISOString().slice(0, 10);
}

// Mismas columnas y mismo orden que backend/app/services/reportes_service.py
// (COLUMNAS_GENERAL / COLUMNAS_FACTURADAS) — el cliente pidió esos
// encabezados exactos, no se tocan.
const COLUMNAS_GENERAL = [
  "ID", "Numero de remision", "Fecha", "Forma de pago", "ODS", "ID del cliente", "Cliente",
  "Proyecto", "Tramo", "Origen", "Destino", "Kilometros", "Vehiculos", "Cama Baja",
  "Hora llegada", "Hora salida", "ID del conductor", "Conductor", "Tipo de transporte",
  "Observaciones", "Id Producto", "Producto", "Cantidad", "Unidad de medida", "Valor Material",
  "Valor Flete", "Numero de viajes", "Valor de comision", "Valor de costo", "Valor cama baja",
  "Remision AGRESUR", "ID del usuario", "Usuario", "Estado",
];

const COLUMNAS_FACTURADAS = [
  "Numero de remision", "Fecha", "Forma de pago", "ODS", "ID cliente", "Cliente", "Proyecto",
  "Tramo", "Origen", "Destino", "Kilometros", "Vehiculos", "Cama Baja", "Hora llegada",
  "Hora salida", "Conductor", "Tipo de transporte", "Usuario", "ID usuario", "ID factura",
  "Usuario Factura", "ID usuario factura", "Número de factura", "Fecha de factura",
  "Valor flete", "Valor Camabaja", "Subtotal", "Valor Material", "Total", "Valor facturado",
  "Valor pendiente", "Estado",
];

const FILTROS_VACIOS = { desde: "", hasta: "", clienteId: null as number | null, proyectoId: null as number | null, estado: "" };

interface ReporteCardProps {
  titulo: string;
  descripcion: string;
  nombreArchivoBase: string;
  columnas: string[];
  descargar: (filtros: ReporteFiltros) => Promise<Blob>;
}

function ReporteCard({ titulo, descripcion, nombreArchivoBase, columnas, descargar }: ReporteCardProps) {
  const toast = useToast();
  const [filtros, setFiltros] = useState(FILTROS_VACIOS);

  const mutation = useMutation({
    mutationFn: () =>
      descargar({
        desde: filtros.desde || undefined,
        hasta: filtros.hasta || undefined,
        cliente_id: filtros.clienteId ?? undefined,
        proyecto_id: filtros.proyectoId ?? undefined,
        estado_facturacion: filtros.estado || undefined,
      }),
    onSuccess: (blob) => {
      guardarBlobComoArchivo(blob, `${nombreArchivoBase}-${hoyISO()}.xlsx`);
      toast.success("Reporte descargado. Si no hay resultados con estos filtros, el Excel trae solo los encabezados.");
    },
    onError: async (error) => {
      toast.error(await getBlobErrorMessage(error, "No se pudo generar el reporte."));
    },
  });

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <div className={styles.cardTitulo}>
          <FileSpreadsheet size={20} strokeWidth={1.75} style={{ color: "var(--accent)" }} />
          <h3 style={{ margin: 0 }}>{titulo}</h3>
        </div>
        <Badge variant="neutral">{columnas.length} columnas</Badge>
      </div>
      <p className={styles.descripcion}>{descripcion}</p>

      <div className={styles.filtros}>
        <Input label="Desde" type="date" value={filtros.desde} onChange={(e) => setFiltros((f) => ({ ...f, desde: e.target.value }))} />
        <Input label="Hasta" type="date" value={filtros.hasta} onChange={(e) => setFiltros((f) => ({ ...f, hasta: e.target.value }))} />
        <AsyncSelect
          label="Cliente"
          endpoint="/api/terceros"
          params={{ tipo: "cliente" }}
          getLabel={(item) => String(item.nombre)}
          value={filtros.clienteId}
          onChange={(id) => setFiltros((f) => ({ ...f, clienteId: id }))}
          placeholder="Todos"
        />
        <AsyncSelect
          label="Proyecto"
          endpoint="/api/catalogos/proyectos"
          getLabel={(item) => String(item.nombre)}
          value={filtros.proyectoId}
          onChange={(id) => setFiltros((f) => ({ ...f, proyectoId: id }))}
          placeholder="Todos"
        />
        <Select
          label="Estado de facturación"
          value={filtros.estado}
          onChange={(e) => setFiltros((f) => ({ ...f, estado: e.target.value }))}
        >
          <option value="">Todos</option>
          <option value="NO_FACTURADA">No facturada</option>
          <option value="FACTURADA_PARCIAL">Facturada parcial</option>
          <option value="FACTURADA">Facturada</option>
        </Select>
      </div>

      <div className={styles.columnasChips}>
        {columnas.map((c) => (
          <span key={c} className={styles.chipColumna}>
            {c}
          </span>
        ))}
      </div>

      <div className={styles.acciones}>
        <Button variant="ghost" onClick={() => setFiltros(FILTROS_VACIOS)} disabled={mutation.isPending}>
          Limpiar
        </Button>
        <Button
          variant="primary"
          leftIcon={<Download size={16} />}
          loading={mutation.isPending}
          onClick={() => mutation.mutate()}
        >
          {mutation.isPending ? "Descargando…" : "Descargar Excel"}
        </Button>
      </div>
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
      <div className={styles.grid}>
        <ReporteCard
          titulo="Reporte general de remisiones"
          descripcion="Una fila por cada línea de producto de la remisión, con los 34 encabezados exactos que pidió el cliente."
          nombreArchivoBase="reporte-remisiones-general"
          columnas={COLUMNAS_GENERAL}
          descargar={descargarReporteGeneral}
        />
        <ReporteCard
          titulo="Reporte de remisiones facturadas"
          descripcion="Una fila por cada facturación activa (una remisión con varias facturas parciales aparece varias veces), 32 encabezados exactos."
          nombreArchivoBase="reporte-remisiones-facturadas"
          columnas={COLUMNAS_FACTURADAS}
          descargar={descargarReporteFacturadas}
        />
      </div>
    </PageHeader>
  );
}
