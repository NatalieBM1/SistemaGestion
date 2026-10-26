import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Plus, Search, X } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  agregarRemisionesAFactura,
  getRemisionesDeFactura,
  getResumenFacturacion,
  listFacturas,
  quitarRemisionDeFactura,
} from "../../api/facturas";
import { getApiErrorMessage } from "../../api/errors";
import { listRemisiones } from "../../api/remisiones";
import {
  Badge,
  Button,
  Checkbox,
  EmptyState,
  IconButton,
  Input,
  Modal,
  PageHeader,
  useToast,
} from "../../components/ui";
import { formatMoney } from "../../lib/format";
import { formatNumeroRemision } from "../../lib/formatNumeroRemision";
import { usePageTitle } from "../../store/pageTitleStore";
import tableStyles from "../../components/ui/Table.module.css";

function PendienteCell({ remisionId }: { remisionId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ["resumen-facturacion", remisionId],
    queryFn: () => getResumenFacturacion(remisionId),
  });
  if (isLoading || !data) return <span style={{ color: "var(--text-disabled)" }}>…</span>;
  return <span className="font-mono-data">{formatMoney(data.saldo_pendiente)}</span>;
}

export function DetalleFactura() {
  const params = useParams<{ numeroFactura: string }>();
  const numeroFactura = decodeURIComponent(params.numeroFactura ?? "");
  const navigate = useNavigate();
  const toast = useToast();
  const queryClient = useQueryClient();

  usePageTitle(`Factura ${formatNumeroRemision(numeroFactura) || numeroFactura}`);

  const [agregarAbierto, setAgregarAbierto] = useState(false);
  const [buscar, setBuscar] = useState("");
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [seleccionadas, setSeleccionadas] = useState<Set<number>>(new Set());
  const [quitarTarget, setQuitarTarget] = useState<number | null>(null);

  const { data: remisiones, isLoading } = useQuery({
    queryKey: ["factura-remisiones", numeroFactura],
    queryFn: () => getRemisionesDeFactura(numeroFactura),
    enabled: Boolean(numeroFactura),
  });

  const { data: facturaInfo } = useQuery({
    queryKey: ["factura-info", numeroFactura],
    queryFn: async () => {
      const resultado = await listFacturas({ page: 1, page_size: 1, numero_factura: numeroFactura });
      return resultado.items.find((f) => f.numero_factura === numeroFactura) ?? resultado.items[0] ?? null;
    },
    enabled: Boolean(numeroFactura),
  });

  const activas = (remisiones ?? []).filter((r) => !r.anulada);
  const valorTotal = activas.reduce((sum, r) => sum + Number(r.valor_facturado), 0);
  const clienteId = activas[0]?.cliente_id ?? null;
  const clienteNombre = activas[0]?.cliente_nombre ?? null;

  const invalidarFactura = () => {
    queryClient.invalidateQueries({ queryKey: ["factura-remisiones", numeroFactura] });
    queryClient.invalidateQueries({ queryKey: ["facturas"] });
  };

  const quitarMutation = useMutation({
    mutationFn: (remisionId: number) => quitarRemisionDeFactura(numeroFactura, remisionId),
    onSuccess: () => {
      invalidarFactura();
      toast.success("Remisión quitada de la factura.");
      setQuitarTarget(null);
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "No se pudo quitar la remisión."));
      setQuitarTarget(null);
    },
  });

  // --- modal "Agregar remisiones" ---
  const { data: candidatas, isLoading: cargandoCandidatas } = useQuery({
    queryKey: ["candidatas-agregar-factura", clienteId, buscar, desde, hasta],
    queryFn: () =>
      listRemisiones({
        page: 1,
        page_size: 50,
        tercero_id: clienteId ?? undefined,
        q: buscar || undefined,
        desde: desde || undefined,
        hasta: hasta || undefined,
      }),
    enabled: agregarAbierto && clienteId != null,
  });

  const idsYaEnFactura = new Set(activas.map((r) => r.remision_id));
  const elegibles = (candidatas?.items ?? []).filter(
    (r) => r.estado_facturacion !== "FACTURADA" && !idsYaEnFactura.has(r.id),
  );

  const toggleCandidata = (id: number) => {
    setSeleccionadas((prev) => {
      const siguiente = new Set(prev);
      if (siguiente.has(id)) siguiente.delete(id);
      else siguiente.add(id);
      return siguiente;
    });
  };

  const todasElegiblesSeleccionadas =
    elegibles.length > 0 && elegibles.every((r) => seleccionadas.has(r.id));

  const alternarTodas = () => {
    setSeleccionadas((prev) => {
      const siguiente = new Set(prev);
      if (todasElegiblesSeleccionadas) {
        elegibles.forEach((r) => siguiente.delete(r.id));
      } else {
        elegibles.forEach((r) => siguiente.add(r.id));
      }
      return siguiente;
    });
  };

  const agregarMutation = useMutation({
    mutationFn: () => agregarRemisionesAFactura(numeroFactura, Array.from(seleccionadas)),
    onSuccess: (respuesta) => {
      invalidarFactura();
      toast.success(
        `${respuesta.remisiones_agregadas} remisión(es) agregada(s) a la factura '${respuesta.numero_factura}'.`,
      );
      cerrarModalAgregar();
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "No se pudo agregar la selección a la factura."));
    },
  });

  const cerrarModalAgregar = () => {
    setAgregarAbierto(false);
    setSeleccionadas(new Set());
    setBuscar("");
    setDesde("");
    setHasta("");
  };

  return (
    <PageHeader
      title={formatNumeroRemision(numeroFactura) || numeroFactura}
      breadcrumb={["Operación", "Facturación", numeroFactura]}
      subtitle="Detalle de la factura: remisiones asociadas y su estado."
      actions={
        <>
          <Button variant="ghost" leftIcon={<ArrowLeft size={16} />} onClick={() => navigate("/facturas")}>
            Volver
          </Button>
          <Button
            variant="primary"
            leftIcon={<Plus size={16} />}
            onClick={() => setAgregarAbierto(true)}
            disabled={clienteId == null}
          >
            Agregar remisiones
          </Button>
        </>
      }
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
          gap: "var(--space-4)",
          padding: "var(--space-4)",
          marginBottom: "var(--space-4)",
          background: "var(--bg-surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-md)",
        }}
      >
        <div>
          <div style={{ fontSize: "var(--text-caption)", color: "var(--text-secondary)" }}>Cliente</div>
          <div style={{ fontWeight: 500 }}>{clienteNombre ?? "—"}</div>
        </div>
        <div>
          <div style={{ fontSize: "var(--text-caption)", color: "var(--text-secondary)" }}>Fecha de factura</div>
          <div style={{ fontWeight: 500 }}>{facturaInfo?.fecha_factura ?? "—"}</div>
        </div>
        <div>
          <div style={{ fontSize: "var(--text-caption)", color: "var(--text-secondary)" }}># Remisiones</div>
          <div style={{ fontWeight: 500 }}>{activas.length}</div>
        </div>
        <div>
          <div style={{ fontSize: "var(--text-caption)", color: "var(--text-secondary)" }}>Valor facturado</div>
          <div style={{ fontWeight: 500 }}>{formatMoney(valorTotal)}</div>
        </div>
      </div>

      {!isLoading && (remisiones ?? []).length === 0 ? (
        <EmptyState title="Sin remisiones" description="Esta factura no tiene remisiones asociadas." />
      ) : (
        <div className={tableStyles.wrapper}>
          <table className={tableStyles.table}>
            <thead>
              <tr>
                <th>Remisión</th>
                <th>Tipo</th>
                <th>Valor facturado</th>
                <th>Estado</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {(remisiones ?? []).map((r) => (
                <tr key={r.id} className={r.anulada ? tableStyles.rowDisabled : undefined}>
                  <td>
                    <Link to={`/remisiones/${r.remision_id}`} style={{ color: "var(--accent)", fontWeight: 500 }} className="font-mono-data">
                      {formatNumeroRemision(r.numero_remision) || r.remision_id}
                    </Link>
                  </td>
                  <td>{r.tipo_facturacion}</td>
                  <td className="font-mono-data">{formatMoney(r.valor_facturado)}</td>
                  <td>
                    <Badge variant={r.anulada ? "danger" : "success"}>{r.anulada ? "Anulada" : "Activa"}</Badge>
                  </td>
                  <td style={{ textAlign: "right" }}>
                    {!r.anulada && (
                      <IconButton
                        label="Quitar de la factura"
                        icon={<X size={16} />}
                        onClick={() => setQuitarTarget(r.remision_id)}
                      />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        open={quitarTarget != null}
        onClose={() => setQuitarTarget(null)}
        title="Quitar remisión de la factura"
        size="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setQuitarTarget(null)}>
              Cancelar
            </Button>
            <Button
              variant="danger"
              loading={quitarMutation.isPending}
              onClick={() => quitarTarget != null && quitarMutation.mutate(quitarTarget)}
            >
              Quitar
            </Button>
          </>
        }
      >
        <p style={{ margin: 0 }}>
          ¿Quitar esta remisión de la factura <strong>{numeroFactura}</strong>? Vuelve a quedar sin
          facturar (o parcialmente facturada, según el resto de sus facturaciones activas).
        </p>
      </Modal>

      <Modal
        open={agregarAbierto}
        onClose={cerrarModalAgregar}
        title="Agregar remisiones a la factura"
        size="lg"
        footer={
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", width: "100%" }}>
            <span style={{ color: "var(--text-secondary)", fontSize: "var(--text-caption)" }}>
              {seleccionadas.size} seleccionada(s)
            </span>
            <div style={{ marginLeft: "auto", display: "flex", gap: "var(--space-2)" }}>
              <Button variant="ghost" onClick={cerrarModalAgregar}>
                Cancelar
              </Button>
              <Button
                variant="primary"
                loading={agregarMutation.isPending}
                disabled={seleccionadas.size === 0 || agregarMutation.isPending}
                onClick={() => agregarMutation.mutate()}
              >
                Agregar {seleccionadas.size || ""} remisión(es)
              </Button>
            </div>
          </div>
        }
      >
        <div style={{ display: "flex", gap: "var(--space-3)", flexWrap: "wrap", marginBottom: "var(--space-3)" }}>
          <div style={{ flex: "1 1 220px" }}>
            <Input
              label="Buscar"
              placeholder="Número o placa…"
              leftElement={<Search size={16} aria-hidden="true" />}
              value={buscar}
              onChange={(e) => setBuscar(e.target.value)}
            />
          </div>
          <div style={{ flex: "0 1 160px" }}>
            <Input label="Desde" type="date" value={desde} onChange={(e) => setDesde(e.target.value)} />
          </div>
          <div style={{ flex: "0 1 160px" }}>
            <Input label="Hasta" type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} />
          </div>
        </div>

        {cargandoCandidatas ? (
          <p style={{ color: "var(--text-secondary)" }}>Cargando remisiones…</p>
        ) : elegibles.length === 0 ? (
          <EmptyState
            title="Sin remisiones disponibles"
            description="No hay remisiones de este cliente sin facturar (o parcialmente facturadas) que coincidan con la búsqueda."
          />
        ) : (
          <div className={tableStyles.wrapper} style={{ maxHeight: 360, overflowY: "auto" }}>
            <table className={tableStyles.table}>
              <thead>
                <tr>
                  <th>
                    <Checkbox
                      aria-label="Seleccionar todas"
                      checked={todasElegiblesSeleccionadas}
                      onChange={alternarTodas}
                    />
                  </th>
                  <th>Número</th>
                  <th>Fecha</th>
                  <th>Placa</th>
                  <th>Estado</th>
                  <th style={{ textAlign: "right" }}>Pendiente</th>
                </tr>
              </thead>
              <tbody>
                {elegibles.map((r) => (
                  <tr
                    key={r.id}
                    className={seleccionadas.has(r.id) ? tableStyles.rowSelected : undefined}
                  >
                    <td>
                      <Checkbox
                        aria-label={`Seleccionar ${formatNumeroRemision(r.numero_remision)}`}
                        checked={seleccionadas.has(r.id)}
                        onChange={() => toggleCandidata(r.id)}
                      />
                    </td>
                    <td className="font-mono-data">{formatNumeroRemision(r.numero_remision)}</td>
                    <td>{r.fecha}</td>
                    <td className="font-mono-data">{r.vehiculo_placa ?? "—"}</td>
                    <td>{r.estado_facturacion}</td>
                    <td style={{ textAlign: "right" }}>
                      <PendienteCell remisionId={r.id} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Modal>
    </PageHeader>
  );
}
