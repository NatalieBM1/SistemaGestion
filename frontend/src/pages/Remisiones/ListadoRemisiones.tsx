import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, FileStack, Pencil, Printer, Plus, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  agregarRemisionesAFactura,
  facturarMultiples,
  resumenFacturarMultiples,
  type ResumenSeleccion,
} from "../../api/facturas";
import { apiClient } from "../../api/client";
import { getApiErrorMessage } from "../../api/errors";
import { copiarRemision, listRemisiones, type Remision } from "../../api/remisiones";
import {
  Button,
  AsyncSelect,
  Checkbox,
  EmptyState,
  EstadoPunto,
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
import { ESTADO_FACTURACION_LABEL } from "../../lib/estadoFacturacion";
import { formatNumeroRemision } from "../../lib/formatNumeroRemision";
import { useOrdenamiento } from "../../hooks/useOrdenamiento";
import listStyles from "./ListadoRemisiones.module.css";

const ESTADO_COLOR: Record<string, "neutral" | "warning" | "success"> = {
  NO_FACTURADA: "neutral",
  FACTURADA_PARCIAL: "warning",
  FACTURADA: "success",
};
import { formatMoney } from "../../lib/format";
import { usePageTitle } from "../../store/pageTitleStore";
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
  const [numeroRemisionCopia, setNumeroRemisionCopia] = useState("");
  const [seleccionadas, setSeleccionadas] = useState<Set<number>>(new Set());
  const [clienteSeleccionado, setClienteSeleccionado] = useState<{ id: number; nombre: string | null } | null>(null);
  const [facturarMultiplesAbierto, setFacturarMultiplesAbierto] = useState(false);
  const [numeroFacturaMultiple, setNumeroFacturaMultiple] = useState("");
  const [fechaFacturaMultiple, setFechaFacturaMultiple] = useState("");
  const [agregarFacturaTarget, setAgregarFacturaTarget] = useState<Remision | null>(null);
  const [numeroFacturaAgregar, setNumeroFacturaAgregar] = useState("");

  const [pageSize, setPageSize] = useState(() => leerFilasPorPaginaGuardadas("remisiones", 20));
  const { ordenamiento, alternar: alternarOrden } = useOrdenamiento();
  const filtros = { q, numeroRemision, placa, factura, proyectoId, desde, hasta, estado, clienteId, pageSize, ordenamiento };
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["remisiones", page, filtros],
    queryFn: () =>
      listRemisiones({
        page,
        page_size: pageSize,
        q: q || undefined,
        numero_remision: numeroRemision || undefined,
        placa: placa || undefined,
        factura: factura || undefined,
        proyecto_id: proyectoId ?? undefined,
        desde: desde || undefined,
        hasta: hasta || undefined,
        estado_facturacion: estado || undefined,
        tercero_id: clienteId ?? undefined,
        ordenar_por: ordenamiento.campo ?? undefined,
        sentido: ordenamiento.sentido ?? undefined,
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

  const { data: prefijos } = useQuery({
    queryKey: ["prefijos-para-copiar"],
    queryFn: async () => {
      const { data } = await apiClient.get<{
        items: { id: number; codigo: string; es_manual: boolean }[];
      }>("/api/catalogos/prefijos", { params: { page_size: 100 } });
      return data.items;
    },
  });
  const prefijoDeLaCopia = prefijos?.find((p) => p.id === copiarTarget?.prefijo_id);
  const copiaEsManual = prefijoDeLaCopia?.es_manual ?? false;

  const copiarMutation = useMutation({
    mutationFn: (copiarProductos: boolean) =>
      copiarRemision(copiarTarget!.id, copiarProductos, copiaEsManual ? numeroRemisionCopia : undefined),
    onSuccess: ({ remision: nueva }) => {
      queryClient.invalidateQueries({ queryKey: ["remisiones"] });
      toast.success(
        `Remisión '${formatNumeroRemision(nueva.numero_remision)}' creada como copia de '${formatNumeroRemision(copiarTarget?.numero_remision)}'.`,
      );
      setCopiarTarget(null);
      setNumeroRemisionCopia("");
      navigate(`/remisiones/${nueva.id}`);
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "No se pudo copiar la remisión."));
    },
  });

  const items = data?.items ?? [];
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  const idsSeleccionados = Array.from(seleccionadas);

  const { data: resumenSeleccion, isLoading: cargandoResumen } = useQuery<ResumenSeleccion>({
    queryKey: ["remisiones-resumen-seleccion", idsSeleccionados],
    queryFn: () => resumenFacturarMultiples(idsSeleccionados),
    enabled: facturarMultiplesAbierto && idsSeleccionados.length > 0,
  });

  const facturarMultiplesMutation = useMutation({
    mutationFn: () =>
      facturarMultiples({
        remision_ids: idsSeleccionados,
        numero_factura: numeroFacturaMultiple.trim(),
        fecha_factura: fechaFacturaMultiple,
      }),
    onSuccess: (respuesta) => {
      queryClient.invalidateQueries({ queryKey: ["remisiones"] });
      toast.success(
        `Factura '${respuesta.numero_factura}' creada para ${respuesta.cantidad_remisiones} remisión(es).`,
      );
      setFacturarMultiplesAbierto(false);
      limpiarSeleccion();
      setNumeroFacturaMultiple("");
      setFechaFacturaMultiple("");
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "No se pudo facturar la selección."));
    },
  });

  const limpiarSeleccion = () => {
    setSeleccionadas(new Set());
    setClienteSeleccionado(null);
  };

  // Escape limpia la selección en toda la pantalla.
  useEffect(() => {
    if (seleccionadas.size === 0) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") limpiarSeleccion();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [seleccionadas.size]);

  const agregarAFacturaMutation = useMutation({
    mutationFn: () => agregarRemisionesAFactura(numeroFacturaAgregar.trim(), [agregarFacturaTarget!.id]),
    onSuccess: (respuesta) => {
      queryClient.invalidateQueries({ queryKey: ["remisiones"] });
      toast.success(
        `Remisión agregada a la factura '${respuesta.numero_factura}' correctamente.`,
      );
      setAgregarFacturaTarget(null);
      setNumeroFacturaAgregar("");
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "No se pudo agregar la remisión a esa factura."));
    },
  });

  const toggleSeleccion = (r: Remision) => {
    setSeleccionadas((prev) => {
      const siguiente = new Set(prev);
      if (siguiente.has(r.id)) {
        siguiente.delete(r.id);
        if (siguiente.size === 0) setClienteSeleccionado(null);
        return siguiente;
      }
      if (clienteSeleccionado && r.cliente_id !== clienteSeleccionado.id) {
        toast.error(
          `"${formatNumeroRemision(r.numero_remision)}" es de otro cliente (${r.cliente_nombre ?? "—"}) — la selección ya tiene remisiones de "${clienteSeleccionado.nombre ?? "—"}".`,
        );
        return prev;
      }
      if (siguiente.size === 0) setClienteSeleccionado({ id: r.cliente_id, nombre: r.cliente_nombre });
      siguiente.add(r.id);
      return siguiente;
    });
  };

  const seleccionablesDeLaPagina = items.filter(
    (r) =>
      r.estado_facturacion !== "FACTURADA" &&
      (!clienteSeleccionado || r.cliente_id === clienteSeleccionado.id),
  );
  const todasLaPaginaSeleccionadas =
    seleccionablesDeLaPagina.length > 0 &&
    seleccionablesDeLaPagina.every((r) => seleccionadas.has(r.id));

  const alternarSeleccionDePagina = () => {
    setSeleccionadas((prev) => {
      const siguiente = new Set(prev);
      if (todasLaPaginaSeleccionadas) {
        seleccionablesDeLaPagina.forEach((r) => siguiente.delete(r.id));
        if (siguiente.size === 0) setClienteSeleccionado(null);
      } else {
        seleccionablesDeLaPagina.forEach((r) => siguiente.add(r.id));
        if (!clienteSeleccionado && seleccionablesDeLaPagina.length > 0) {
          const primera = seleccionablesDeLaPagina[0];
          setClienteSeleccionado({ id: primera.cliente_id, nombre: primera.cliente_nombre });
        }
      }
      return siguiente;
    });
  };

  const columns: TableColumn<Remision>[] = [
    {
      key: "seleccion",
      header: (
        <Checkbox
          aria-label="Seleccionar todas en esta página"
          checked={todasLaPaginaSeleccionadas}
          disabled={seleccionablesDeLaPagina.length === 0}
          onChange={alternarSeleccionDePagina}
        />
      ),
      render: (r) => (
        <Checkbox
          aria-label={`Seleccionar remisión ${formatNumeroRemision(r.numero_remision)}`}
          checked={seleccionadas.has(r.id)}
          disabled={r.estado_facturacion === "FACTURADA"}
          onChange={() => toggleSeleccion(r)}
        />
      ),
    },
    {
      key: "numero_remision",
      header: "Número",
      monoData: true,
      sortField: "numero_remision",
      render: (r) => (
        <Link to={`/remisiones/${r.id}`} style={{ color: "var(--accent)", fontWeight: 500 }}>
          {formatNumeroRemision(r.numero_remision)}
        </Link>
      ),
    },
    { key: "fecha", header: "Fecha", sortField: "fecha", render: (r) => r.fecha },
    { key: "cliente", header: "Cliente", truncate: true, sortField: "cliente", render: (r) => r.cliente_nombre ?? "—" },
    {
      key: "estado",
      header: "Estado",
      sortField: "estado",
      render: (r) => (
        <EstadoPunto color={ESTADO_COLOR[r.estado_facturacion] ?? "neutral"}>
          {ESTADO_FACTURACION_LABEL[r.estado_facturacion] ?? r.estado_facturacion}
        </EstadoPunto>
      ),
    },
    { key: "placa", header: "Placa", monoData: true, sortField: "placa", render: (r) => r.vehiculo_placa ?? "—" },
    { key: "valor_total", sortField: "valor_total", header: "Valor total", align: "right", render: (r) => formatMoney(r.valor_total) },
    {
      key: "acciones",
      header: "Acciones",
      align: "right",
      render: (r) => (
        <div className={tableStyles.actionsCell}>
          <IconButton
            variant="accent"
            label="Editar remisión"
            icon={<Pencil size={14} strokeWidth={2} />}
            onClick={() => navigate(`/remisiones/${r.id}`)}
          />
          <IconButton
            label="Copiar remisión"
            icon={<Copy size={16} />}
            onClick={() => setCopiarTarget(r)}
          />
          <IconButton
            label="Imprimir remisión"
            icon={<Printer size={16} />}
            onClick={() => window.open(`/remisiones/${r.id}/imprimir`, "_blank")}
          />
          {r.estado_facturacion !== "FACTURADA" && (
            <IconButton
              label="Agregar a factura existente"
              icon={<FileStack size={16} />}
              onClick={() => setAgregarFacturaTarget(r)}
            />
          )}
        </div>
      ),
    },
  ];

  const getRowClassName = (r: Remision) => {
    if (r.estado_facturacion === "FACTURADA") return tableStyles.rowDisabled;
    if (seleccionadas.has(r.id)) return tableStyles.rowSelected;
    return undefined;
  };

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
          placeholder="GTS-6525"
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

      {isError ? (
        <EmptyState
          icon={<Search size={32} strokeWidth={1.5} />}
          title="No se pudo cargar el listado"
          description="Hubo un problema al traer las remisiones. Intenta de nuevo."
          action={
            <Button variant="primary" onClick={() => refetch()}>
              Reintentar
            </Button>
          }
        />
      ) : !isLoading && items.length === 0 ? (
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
          <Table
            columns={columns}
            data={items}
            getRowId={(row) => row.id}
            isLoading={isLoading}
            getRowClassName={getRowClassName}
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
                  guardarFilasPorPagina("remisiones", n);
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

      <Modal
        open={copiarTarget != null}
        onClose={() => {
          setCopiarTarget(null);
          setNumeroRemisionCopia("");
        }}
        title="Duplicar remisión"
        size="sm"
        footer={
          <>
            <Button
              variant="ghost"
              loading={copiarMutation.isPending && copiarMutation.variables === false}
              disabled={copiarMutation.isPending || (copiaEsManual && !numeroRemisionCopia.trim())}
              onClick={() => copiarMutation.mutate(false)}
            >
              Solo datos generales
            </Button>
            <Button
              variant="primary"
              loading={copiarMutation.isPending && copiarMutation.variables === true}
              disabled={copiarMutation.isPending || (copiaEsManual && !numeroRemisionCopia.trim())}
              onClick={() => copiarMutation.mutate(true)}
            >
              Copiar con productos
            </Button>
          </>
        }
      >
        <p style={{ margin: 0, color: "var(--text-primary)" }}>
          Se creará una nueva remisión con los mismos datos generales de <strong>{formatNumeroRemision(copiarTarget?.numero_remision)}</strong>.
          ¿Copiar también los productos asociados a esta remisión?
        </p>
        {copiaEsManual && (
          <div style={{ marginTop: "var(--space-3)" }}>
            <Input
              label="Número de remisión de la copia (manual)"
              placeholder="Ej: 00123"
              hint={`El prefijo '${prefijoDeLaCopia?.codigo}' es manual: no se autogenera, hay que escribirlo.`}
              value={numeroRemisionCopia}
              onChange={(e) => setNumeroRemisionCopia(e.target.value)}
            />
          </div>
        )}
      </Modal>


      <Modal
        open={facturarMultiplesAbierto}
        onClose={() => setFacturarMultiplesAbierto(false)}
        title="Facturar remisiones seleccionadas"
        footer={
          <>
            <Button variant="ghost" onClick={() => setFacturarMultiplesAbierto(false)}>
              Cancelar
            </Button>
            <Button
              variant="primary"
              loading={facturarMultiplesMutation.isPending}
              disabled={
                !resumenSeleccion?.puede_facturar ||
                !numeroFacturaMultiple.trim() ||
                !fechaFacturaMultiple
              }
              onClick={() => facturarMultiplesMutation.mutate()}
            >
              Confirmar factura
            </Button>
          </>
        }
      >
        {cargandoResumen ? (
          <p>Calculando resumen…</p>
        ) : resumenSeleccion && !resumenSeleccion.puede_facturar ? (
          <>
            <p style={{ color: "var(--danger)", fontWeight: 500 }}>
              No se puede facturar esta selección:
            </p>
            <ul>
              {resumenSeleccion.items.map((item) => (
                <li key={item.remision_id}>
                  <strong>{formatNumeroRemision(item.numero_remision)}</strong>: {item.motivo_error}
                </li>
              ))}
            </ul>
          </>
        ) : resumenSeleccion ? (
          <>
            <p style={{ margin: 0 }}>
              Cliente: <strong>{resumenSeleccion.cliente_nombre}</strong>
              <br />
              {resumenSeleccion.cantidad_remisiones} remisión(es) · Valor total:{" "}
              <strong>{formatMoney(resumenSeleccion.valor_total)}</strong>
            </p>
            <div style={{ display: "grid", gap: "var(--space-3)", marginTop: "var(--space-4)" }}>
              <Input
                label="Número de factura"
                placeholder="Ej: F-7-468"
                hint="Formato: una letra mayúscula, guion, dígitos (ej. F-1234 o F-7-468)."
                value={numeroFacturaMultiple}
                onChange={(e) => setNumeroFacturaMultiple(e.target.value)}
              />
              <Input
                label="Fecha de factura"
                type="date"
                value={fechaFacturaMultiple}
                onChange={(e) => setFechaFacturaMultiple(e.target.value)}
              />
            </div>
          </>
        ) : null}
      </Modal>

      <Modal
        open={agregarFacturaTarget != null}
        onClose={() => {
          setAgregarFacturaTarget(null);
          setNumeroFacturaAgregar("");
        }}
        title="Agregar a factura existente"
        size="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setAgregarFacturaTarget(null)}>
              Cancelar
            </Button>
            <Button
              variant="primary"
              loading={agregarAFacturaMutation.isPending}
              disabled={!numeroFacturaAgregar.trim() || agregarAFacturaMutation.isPending}
              onClick={() => agregarAFacturaMutation.mutate()}
            >
              Agregar
            </Button>
          </>
        }
      >
        <p style={{ margin: "0 0 var(--space-3)", color: "var(--text-primary)" }}>
          Agregar la remisión{" "}
          <strong>{agregarFacturaTarget && formatNumeroRemision(agregarFacturaTarget.numero_remision)}</strong>{" "}
          a una factura ya existente (debe ser del mismo cliente).
        </p>
        <Input
          label="Número de factura"
          placeholder="Ej: F-7-468"
          value={numeroFacturaAgregar}
          onChange={(e) => setNumeroFacturaAgregar(e.target.value)}
        />
      </Modal>

      {seleccionadas.size > 0 && (
        <div className={listStyles.barraFlotante}>
          <span>
            <strong>{seleccionadas.size}</strong> remisión(es) seleccionada(s)
            {clienteSeleccionado && <> · {clienteSeleccionado.nombre ?? "—"}</>}
          </span>
          <Button variant="ghost" onClick={limpiarSeleccion}>
            Limpiar
          </Button>
          <Button variant="primary" onClick={() => setFacturarMultiplesAbierto(true)}>
            Facturar seleccionadas
          </Button>
        </div>
      )}
    </PageHeader>
  );
}
