import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, Plus, Printer, Search } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getApiErrorMessage } from "../../api/errors";
import { copiarRemision, listRemisiones, type Remision } from "../../api/remisiones";
import {
  Button,
  AsyncSelect,
  EmptyState,
  EstadoPunto,
  FilterPanel,
  IconButton,
  Input,
  Modal,
  PageHeader,
  Table,
  type TableColumn,
  useToast,
} from "../../components/ui";
import { ESTADO_FACTURACION_LABEL } from "../../lib/estadoFacturacion";
import listStyles from "./ListadoRemisiones.module.css";

const ESTADO_COLOR: Record<string, "neutral" | "warning" | "success"> = {
  NO_FACTURADA: "neutral",
  FACTURADA_PARCIAL: "warning",
  FACTURADA: "success",
};
import { formatMoney } from "../../lib/format";
import { usePageTitle } from "../../store/pageTitleStore";
import { ProductosModal } from "./ProductosModal";
import styles from "../../components/CatalogoCRUD.module.css";
import tableStyles from "../../components/ui/Table.module.css";


export function ListadoRemisiones() {
  usePageTitle("Remisiones");
  const navigate = useNavigate();
  const toast = useToast();
  const queryClient = useQueryClient();

  const [page, setPage] = useState(1);
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [q, setQ] = useState("");
  const [numeroRemision, setNumeroRemision] = useState("");
  const [placa, setPlaca] = useState("");
  const [factura, setFactura] = useState("");
  const [proyectoId, setProyectoId] = useState<number | null>(null);
  const [estado, setEstado] = useState("");
  const [clienteId, setClienteId] = useState<number | null>(null);
  const [copiarTarget, setCopiarTarget] = useState<Remision | null>(null);
  const [productosTarget, setProductosTarget] = useState<Remision | null>(null);

  const filtros = { q, numeroRemision, placa, factura, proyectoId, desde, hasta, estado, clienteId };
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["remisiones", page, filtros],
    queryFn: () =>
      listRemisiones({
        page,
        q: q || undefined,
        numero_remision: numeroRemision || undefined,
        placa: placa || undefined,
        factura: factura || undefined,
        proyecto_id: proyectoId ?? undefined,
        desde: desde || undefined,
        hasta: hasta || undefined,
        estado_facturacion: estado || undefined,
        tercero_id: clienteId ?? undefined,
      }),
  });

  const limpiarFiltros = () => {
    setQ("");
    setNumeroRemision("");
    setPlaca("");
    setFactura("");
    setProyectoId(null);
    setDesde("");
    setHasta("");
    setEstado("");
    setClienteId(null);
    setPage(1);
  };

  const copiarMutation = useMutation({
    mutationFn: (copiarProductos: boolean) => copiarRemision(copiarTarget!.id, copiarProductos),
    onSuccess: ({ remision: nueva }) => {
      queryClient.invalidateQueries({ queryKey: ["remisiones"] });
      toast.success(`Remisión '${nueva.numero_remision}' creada como copia de '${copiarTarget?.numero_remision}'.`);
      setCopiarTarget(null);
      navigate(`/remisiones/${nueva.id}`);
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "No se pudo copiar la remisión."));
      setCopiarTarget(null);
    },
  });

  const items = data?.items ?? [];
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  const columns: TableColumn<Remision>[] = [
    {
      key: "numero_remision",
      header: "Número",
      monoData: true,
      render: (r) => (
        <Link to={`/remisiones/${r.id}`} style={{ color: "var(--accent)", fontWeight: 500 }}>
          {r.numero_remision}
        </Link>
      ),
    },
    { key: "fecha", header: "Fecha", render: (r) => r.fecha },
    { key: "cliente", header: "Cliente", truncate: true, render: (r) => r.cliente_nombre ?? "—" },
    {
      key: "estado",
      header: "Estado",
      render: (r) => (
        <EstadoPunto color={ESTADO_COLOR[r.estado_facturacion] ?? "neutral"}>
          {ESTADO_FACTURACION_LABEL[r.estado_facturacion] ?? r.estado_facturacion}
        </EstadoPunto>
      ),
    },
    { key: "placa", header: "Placa", monoData: true, render: (r) => r.vehiculo_placa ?? "—" },
    { key: "valor_total", header: "Valor total", align: "right", render: (r) => formatMoney(r.valor_total) },
    {
      key: "acciones",
      header: "",
      align: "right",
      render: (r) => (
        <div className={tableStyles.actionsCell}>
          <IconButton
            variant="accent"
            label="Agregar producto"
            icon={<Plus size={14} strokeWidth={2.5} />}
            onClick={() => setProductosTarget(r)}
          />
          <IconButton
            label="Duplicar remisión"
            icon={<Copy size={16} />}
            onClick={() => setCopiarTarget(r)}
          />
          <IconButton
            label="Imprimir remisión"
            icon={<Printer size={16} />}
            onClick={() => window.open(`/remisiones/${r.id}/imprimir`, "_blank")}
          />
        </div>
      ),
    },
  ];

  return (
    <PageHeader
      title="Remisiones"
      breadcrumb={["Operación", "Remisiones"]}
      subtitle="Consulta, crea y da seguimiento a las remisiones."
      actions={
        <Button variant="primary" leftIcon={<Plus size={16} />} onClick={() => navigate("/remisiones/nueva")}>
          Nueva remisión
        </Button>
      }
    >
      <FilterPanel
        search={
          <Input
            aria-label="Buscar remisiones"
            placeholder="Buscar por cliente, número, placa, proyecto o factura…"
            leftElement={<Search size={18} aria-hidden="true" />}
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(1);
            }}
          />
        }
        footer={
          <>
            <div className={listStyles.chips}>
              <label
                className={[listStyles.chip, estado ? listStyles.chipActive : ""]
                  .filter(Boolean)
                  .join(" ")}
              >
                Estado
                <select
                  aria-label="Filtrar por estado"
                  value={estado}
                  onChange={(e) => {
                    setEstado(e.target.value);
                    setPage(1);
                  }}
                  className={listStyles.chipSelect}
                >
                  <option value="">Todos</option>
                  <option value="NO_FACTURADA">No facturada</option>
                  <option value="FACTURADA_PARCIAL">Facturada parcial</option>
                  <option value="FACTURADA">Facturada</option>
                </select>
              </label>
              <div
                className={[listStyles.chip, clienteId != null ? listStyles.chipActive : ""]
                  .filter(Boolean)
                  .join(" ")}
              >
                Cliente
                <span className={listStyles.chipAsync}>
                  <AsyncSelect
                    aria-label="Filtrar por cliente"
                    endpoint="/api/terceros"
                    params={{ tipo: "cliente" }}
                    getLabel={(item) => String(item.nombre)}
                    value={clienteId}
                    onChange={(id) => {
                      setClienteId(id);
                      setPage(1);
                    }}
                    placeholder="Todos"
                  />
                </span>
              </div>
            </div>
            <div style={{ display: "flex", gap: "var(--space-2)", alignItems: "center" }}>
              <Button variant="ghost" onClick={limpiarFiltros}>
                Limpiar
              </Button>
              <Button variant="primary" leftIcon={<Search size={16} />} onClick={() => refetch()}>
                Buscar
              </Button>
            </div>
          </>
        }
      >
        <Input
          label="Número de remisión"
          placeholder="GTM-000000"
          value={numeroRemision}
          onChange={(e) => {
            setNumeroRemision(e.target.value);
            setPage(1);
          }}
        />
        <Input
          label="Placa"
          placeholder="ABC123"
          value={placa}
          onChange={(e) => {
            setPlaca(e.target.value);
            setPage(1);
          }}
        />
        <AsyncSelect
          label="Proyecto"
          endpoint="/api/catalogos/proyectos"
          getLabel={(item) => String(item.nombre ?? "")}
          value={proyectoId}
          onChange={(id) => {
            setProyectoId(id);
            setPage(1);
          }}
          placeholder="Todos"
        />
        <Input
          label="Número de factura"
          placeholder="FV-0000"
          value={factura}
          onChange={(e) => {
            setFactura(e.target.value);
            setPage(1);
          }}
        />
        <Input
          label="Desde"
          type="date"
          value={desde}
          onChange={(e) => {
            setDesde(e.target.value);
            setPage(1);
          }}
        />
        <Input
          label="Hasta"
          type="date"
          value={hasta}
          onChange={(e) => {
            setHasta(e.target.value);
            setPage(1);
          }}
        />
      </FilterPanel>

      {!isLoading && items.length === 0 ? (
        <EmptyState
          icon={<Search size={32} strokeWidth={1.5} />}
          title="Sin remisiones"
          description="No encontramos remisiones que coincidan con los filtros."
          action={
            <Button variant="primary" onClick={() => navigate("/remisiones/nueva")}>
              Nueva remisión
            </Button>
          }
        />
      ) : (
        <>
          <Table columns={columns} data={items} getRowId={(row) => row.id} isLoading={isLoading} />
          {data && data.total > data.page_size && (
            <div className={styles.pagination}>
              <span>
                Página {data.page} de {totalPages} · {data.total} registros
              </span>
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

      <Modal
        open={copiarTarget != null}
        onClose={() => setCopiarTarget(null)}
        title="Duplicar remisión"
        size="sm"
        footer={
          <>
            <Button
              variant="ghost"
              loading={copiarMutation.isPending && copiarMutation.variables === false}
              disabled={copiarMutation.isPending}
              onClick={() => copiarMutation.mutate(false)}
            >
              Solo datos generales
            </Button>
            <Button
              variant="primary"
              loading={copiarMutation.isPending && copiarMutation.variables === true}
              disabled={copiarMutation.isPending}
              onClick={() => copiarMutation.mutate(true)}
            >
              Copiar con productos
            </Button>
          </>
        }
      >
        <p style={{ margin: 0, color: "var(--text-primary)" }}>
          Se creará una nueva remisión con los mismos datos generales de <strong>{copiarTarget?.numero_remision}</strong>.
          ¿Copiar también los productos asociados a esta remisión?
        </p>
      </Modal>

      {productosTarget && (
        <ProductosModal
          remisionId={productosTarget.id}
          open={productosTarget != null}
          onClose={() => setProductosTarget(null)}
        />
      )}
    </PageHeader>
  );
}
