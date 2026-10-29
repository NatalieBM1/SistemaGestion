import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Calendar, FileText, Pencil, Search, Upload } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { getApiErrorMessage } from "../../api/errors";
import { actualizarFactura, listFacturas, type Factura } from "../../api/facturas";
import {
  Button,
  EmptyState,
  FilterPanel,
  IconButton,
  Input,
  Modal,
  PageHeader,
  SelectorFilasPorPagina,
  Table,
  type TableColumn,
  guardarFilasPorPagina,
  leerFilasPorPaginaGuardadas,
  rangoRegistros,
  useToast,
} from "../../components/ui";
import { useOrdenamiento } from "../../hooks/useOrdenamiento";
import { canWrite } from "../../lib/permissions";
import { formatMoney } from "../../lib/format";
import { useAuthStore } from "../../store/authStore";
import { usePageTitle } from "../../store/pageTitleStore";
import styles from "../../components/CatalogoCRUD.module.css";

interface ActualizarFormValues {
  numero_factura_nuevo: string;
  fecha_factura_nueva: string;
}

export function ListadoFacturas() {
  usePageTitle("Facturación");
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const puedeEscribir = canWrite(user);

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(() => leerFilasPorPaginaGuardadas("facturas", 20));
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [numeroFactura, setNumeroFactura] = useState("");
  const [editTarget, setEditTarget] = useState<Factura | null>(null);
  const { ordenamiento, alternar: alternarOrden } = useOrdenamiento();

  const queryKey = ["facturas", page, pageSize, desde, hasta, numeroFactura, ordenamiento];
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey,
    queryFn: () =>
      listFacturas({
        page,
        page_size: pageSize,
        desde: desde || undefined,
        hasta: hasta || undefined,
        numero_factura: numeroFactura || undefined,
        ordenar_por: ordenamiento.campo ?? undefined,
        sentido: ordenamiento.sentido ?? undefined,
      }),
  });

  const items = data?.items ?? [];
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  const columns: TableColumn<Factura>[] = [
    {
      key: "numero_factura",
      header: "Número de factura",
      monoData: true,
      sortField: "numero_factura",
      render: (f) => (
        <Link to={`/facturas/${encodeURIComponent(f.numero_factura)}`} style={{ color: "var(--accent)", fontWeight: 500 }}>
          {f.numero_factura}
        </Link>
      ),
    },
    { key: "fecha_factura", header: "Fecha", sortField: "fecha_factura", render: (f) => f.fecha_factura },
    {
      key: "cantidad_remisiones",
      header: "Remisiones",
      sortField: "cantidad_remisiones",
      render: (f) => f.cantidad_remisiones,
    },
    {
      key: "valor_total_facturado",
      sortField: "valor_total_facturado",
      header: "Valor total facturado",
      align: "right",
      render: (f) => formatMoney(f.valor_total_facturado),
    },
    {
      key: "acciones",
      header: "",
      align: "right",
      render: (f) => (
        <IconButton
          label={puedeEscribir ? "Actualizar factura" : "No tienes permiso para esta acción"}
          icon={<Pencil size={16} />}
          onClick={() => setEditTarget(f)}
          disabled={!puedeEscribir}
        />
      ),
    },
  ];

  return (
    <PageHeader
      title="Facturación"
      breadcrumb={["Operación", "Facturación"]}
      actions={
        <Button variant="secondary" leftIcon={<Upload size={16} />} onClick={() => navigate("/facturas/cargas-excel")}>
          Cargas por Excel
        </Button>
      }
    >
      <FilterPanel>
        <Input
          label="Desde"
          type="date"
          leftElement={<Calendar size={16} aria-hidden="true" />}
          value={desde}
          onChange={(e) => {
            setDesde(e.target.value);
            setPage(1);
          }}
        />
        <Input
          label="Hasta"
          type="date"
          leftElement={<Calendar size={16} aria-hidden="true" />}
          value={hasta}
          onChange={(e) => {
            setHasta(e.target.value);
            setPage(1);
          }}
        />
        <Input
          label="Número de factura"
          placeholder="Buscar…"
          leftElement={<FileText size={16} aria-hidden="true" />}
          value={numeroFactura}
          onChange={(e) => {
            setNumeroFactura(e.target.value);
            setPage(1);
          }}
        />
      </FilterPanel>

      {isError ? (
        <EmptyState
          icon={<Search size={32} strokeWidth={1.5} />}
          title="No se pudo cargar el listado"
          description="Hubo un problema al traer los datos. Intenta de nuevo."
          action={
            <Button variant="primary" onClick={() => refetch()}>
              Reintentar
            </Button>
          }
        />
      ) : !isLoading && items.length === 0 ? (
        <EmptyState
          icon={<Search size={32} strokeWidth={1.5} />}
          title="Sin facturas"
          description="No encontramos facturas que coincidan con los filtros."
        />
      ) : (
        <>
          <Table
            columns={columns}
            data={items}
            getRowId={(row) => row.numero_factura}
            isLoading={isLoading}
            ordenamiento={ordenamiento}
            onOrdenar={(campo) => {
              alternarOrden(campo);
              setPage(1);
            }}
          />
          {data && (
            <div className={styles.pagination}>
              <span>{rangoRegistros(data.page, data.page_size, data.total)}</span>
              <SelectorFilasPorPagina
                value={pageSize}
                onChange={(n) => {
                  setPageSize(n);
                  guardarFilasPorPagina("facturas", n);
                  setPage(1);
                }}
              />
              <Button variant="ghost" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>
                Anterior
              </Button>
              <Button
                variant="ghost"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
              >
                Siguiente
              </Button>
            </div>
          )}
        </>
      )}

      <ActualizarFacturaModal factura={editTarget} onClose={() => setEditTarget(null)} />
    </PageHeader>
  );
}

function ActualizarFacturaModal({ factura, onClose }: { factura: Factura | null; onClose: () => void }) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [resultado, setResultado] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ActualizarFormValues>({ defaultValues: { numero_factura_nuevo: "", fecha_factura_nueva: "" } });

  const mutation = useMutation({
    mutationFn: (payload: { numero_factura_actual: string; numero_factura_nuevo?: string; fecha_factura_nueva?: string }) =>
      actualizarFactura(payload),
    onSuccess: (respuesta) => {
      queryClient.invalidateQueries({ queryKey: ["facturas"] });
      queryClient.invalidateQueries({ queryKey: ["remisiones"] });
      setResultado(
        `Factura actualizada a '${respuesta.numero_factura}'. Se vieron afectadas ${respuesta.remisiones_afectadas} remisión(es).`,
      );
      toast.success("Factura actualizada correctamente.");
    },
    onError: (err) => setError(getApiErrorMessage(err, "No se pudo actualizar la factura.")),
  });

  const onSubmit = handleSubmit((values) => {
    if (!factura) return;
    setError(null);
    setResultado(null);
    mutation.mutate({
      numero_factura_actual: factura.numero_factura,
      numero_factura_nuevo: values.numero_factura_nuevo.trim() || undefined,
      fecha_factura_nueva: values.fecha_factura_nueva || undefined,
    });
  });

  const handleClose = () => {
    setError(null);
    setResultado(null);
    reset();
    onClose();
  };

  return (
    <Modal
      open={Boolean(factura)}
      onClose={handleClose}
      title={`Actualizar factura ${factura?.numero_factura ?? ""}`}
      footer={
        <>
          <Button type="button" variant="ghost" onClick={handleClose}>
            Cerrar
          </Button>
          <Button type="submit" form="actualizar-factura-form" variant="primary" loading={mutation.isPending}>
            Actualizar
          </Button>
        </>
      }
    >
      <form id="actualizar-factura-form" onSubmit={onSubmit} className={styles.form} noValidate>
        {error && <div className={styles.formError}>{error}</div>}
        {resultado && (
          <div className={styles.confirmText} style={{ color: "var(--success)" }}>
            {resultado}
          </div>
        )}

        <Input label="Número de factura actual" value={factura?.numero_factura ?? ""} disabled monoData leftElement={<FileText size={16} aria-hidden="true" />} />
        <Input
          label="Nuevo número de factura"
          placeholder="Ej: F-7-468"
          hint="Déjalo vacío para no cambiarlo."
          leftElement={<FileText size={16} aria-hidden="true" />}
          error={errors.numero_factura_nuevo?.message}
          {...register("numero_factura_nuevo")}
        />
        <Input
          label="Nueva fecha de factura"
          type="date"
          hint="Déjalo vacío para no cambiarla."
          leftElement={<Calendar size={16} aria-hidden="true" />}
          {...register("fecha_factura_nueva")}
        />
      </form>
    </Modal>
  );
}
