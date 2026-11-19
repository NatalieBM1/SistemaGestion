import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Ban } from "lucide-react";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { getApiErrorMessage } from "../../api/errors";
import {
  anularFacturacion,
  facturarRemision,
  getHistorialFacturacion,
  getResumenFacturacion,
} from "../../api/facturas";
import { Badge, Button, Input, InputFecha, InputNumero, Modal, Select, useToast } from "../../components/ui";
import { esFacturable } from "../../lib/estadoFacturacion";
import { ESTADO_FACTURACION_LABEL, ESTADO_FACTURACION_VARIANT } from "../../lib/estadoFacturacion";
import { formatCOP } from "../../lib/format";
import styles from "../../components/CatalogoCRUD.module.css";
import tableStyles from "../../components/ui/Table.module.css";

interface FacturarFormValues {
  numero_factura: string;
  fecha_factura: string;
  tipo: "TOTAL" | "PARCIAL";
  valor_facturado: string;
}

export function FacturacionPanel({
  remisionId,
  puedeEscribir,
}: {
  remisionId: number;
  puedeEscribir: boolean;
}) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [anularTarget, setAnularTarget] = useState<{ id: number; numeroFactura: string } | null>(null);

  const { data: resumen } = useQuery({
    queryKey: ["resumen-facturacion", remisionId],
    queryFn: () => getResumenFacturacion(remisionId),
  });

  const { data: historial } = useQuery({
    queryKey: ["historial-facturacion", remisionId],
    queryFn: () => getHistorialFacturacion(remisionId),
  });

  const invalidateTodo = () => {
    queryClient.invalidateQueries({ queryKey: ["resumen-facturacion", remisionId] });
    queryClient.invalidateQueries({ queryKey: ["historial-facturacion", remisionId] });
    queryClient.invalidateQueries({ queryKey: ["remision", remisionId] });
    queryClient.invalidateQueries({ queryKey: ["remisiones"] });
  };

  const anularMutation = useMutation({
    mutationFn: (id: number) => anularFacturacion(remisionId, id),
    onSuccess: () => {
      invalidateTodo();
      toast.success("Facturación anulada correctamente.");
      setAnularTarget(null);
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "No se pudo anular la facturación."));
      setAnularTarget(null);
    },
  });

  const estado = resumen?.estado_facturacion ?? "NO_FACTURADA";
  const puedeFacturar = puedeEscribir && esFacturable(estado);

  return (
    <div style={{ marginTop: "var(--space-6)" }}>
      <div className={styles.toolbar}>
        <h3 style={{ margin: 0 }}>Facturación</h3>
        <Button
          variant="primary"
          onClick={() => setModalOpen(true)}
          disabled={!puedeFacturar}
          title={
            estado === "FACTURADA"
              ? "La remisión ya está totalmente facturada."
              : estado === "NO_APLICA"
                ? "La remisión está marcada como «No aplica facturación»."
                : undefined
          }
        >
          Facturar
        </Button>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
          gap: "var(--space-4)",
          padding: "var(--space-4)",
          background: "var(--bg-surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-md)",
          marginBottom: "var(--space-4)",
        }}
      >
        <div>
          <div style={{ fontSize: "var(--text-caption)", color: "var(--text-secondary)" }}>Estado</div>
          <Badge variant={ESTADO_FACTURACION_VARIANT[estado] ?? "neutral"}>
            {ESTADO_FACTURACION_LABEL[estado] ?? estado}
          </Badge>
        </div>
        <div>
          <div style={{ fontSize: "var(--text-caption)", color: "var(--text-secondary)" }}>Valor total</div>
          <div className="cifras">{resumen ? formatCOP(resumen.valor_total) : "—"}</div>
        </div>
        <div>
          <div style={{ fontSize: "var(--text-caption)", color: "var(--text-secondary)" }}>Facturado</div>
          <div className="cifras">{resumen ? formatCOP(resumen.valor_facturado) : "—"}</div>
        </div>
        <div>
          <div style={{ fontSize: "var(--text-caption)", color: "var(--text-secondary)" }}>Saldo pendiente</div>
          <div className="cifras">{resumen ? formatCOP(resumen.saldo_pendiente) : "—"}</div>
        </div>
      </div>

      {!historial || historial.length === 0 ? (
        <p style={{ color: "var(--text-secondary)" }}>Sin facturaciones registradas todavía.</p>
      ) : (
        <div className={tableStyles.wrapper}>
          <table className={tableStyles.table}>
            <thead>
              <tr>
                <th>Factura</th>
                <th>Fecha</th>
                <th>Tipo</th>
                <th>Valor</th>
                <th>Estado</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {historial.map((h) => (
                <tr
                  key={h.id}
                  style={{
                    opacity: h.anulada ? 0.55 : 1,
                    textDecoration: h.anulada ? "line-through" : "none",
                  }}
                >
                  <td className="cifras">{h.numero_factura}</td>
                  <td>{h.fecha_factura}</td>
                  <td>{h.tipo_facturacion}</td>
                  <td className="cifras">{formatCOP(h.valor_facturado)}</td>
                  <td style={{ textDecoration: "none" }}>
                    <Badge variant={h.anulada ? "danger" : "success"}>{h.anulada ? "Anulada" : "Activa"}</Badge>
                  </td>
                  <td className={tableStyles.alignRight} style={{ textDecoration: "none" }}>
                    {!h.anulada && (
                      <button
                        type="button"
                        onClick={() => setAnularTarget({ id: h.id, numeroFactura: h.numero_factura })}
                        disabled={!puedeEscribir}
                        title={puedeEscribir ? "Anular facturación" : "No tienes permiso para esta acción"}
                        aria-label="Anular facturación"
                        className={[tableStyles.actionButton, tableStyles.danger].join(" ")}
                      >
                        <Ban size={16} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <FacturarModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        remisionId={remisionId}
        saldoPendiente={resumen?.saldo_pendiente ?? "0"}
        onSuccess={invalidateTodo}
      />

      <Modal
        open={Boolean(anularTarget)}
        onClose={() => setAnularTarget(null)}
        title="Confirmar anulación"
        size="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setAnularTarget(null)}>
              Cancelar
            </Button>
            <Button
              variant="danger"
              loading={anularMutation.isPending}
              onClick={() => anularTarget && anularMutation.mutate(anularTarget.id)}
            >
              Anular
            </Button>
          </>
        }
      >
        <p className={styles.confirmText}>
          ¿Seguro que quieres anular la facturación de la factura{" "}
          <strong>{anularTarget?.numeroFactura}</strong>? El saldo pendiente de la remisión se recalculará.
        </p>
      </Modal>
    </div>
  );
}

function FacturarModal({
  open,
  onClose,
  remisionId,
  saldoPendiente,
  onSuccess,
}: {
  open: boolean;
  onClose: () => void;
  remisionId: number;
  saldoPendiente: string;
  onSuccess: () => void;
}) {
  const toast = useToast();
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    control,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<FacturarFormValues>({
    defaultValues: {
      numero_factura: "",
      fecha_factura: new Date().toISOString().slice(0, 10),
      tipo: "TOTAL",
      valor_facturado: "",
    },
  });

  const tipo = watch("tipo");

  const mutation = useMutation({
    mutationFn: (payload: { numero_factura: string; fecha_factura: string; tipo: "TOTAL" | "PARCIAL"; valor_facturado?: number }) =>
      facturarRemision(remisionId, payload),
    onSuccess: (respuesta) => {
      onSuccess();
      toast.success(`Remisión facturada en '${respuesta.numero_factura}' correctamente.`);
      reset();
      onClose();
    },
    onError: (err) => setError(getApiErrorMessage(err, "No se pudo facturar la remisión.")),
  });

  const onSubmit = handleSubmit((values) => {
    setError(null);
    mutation.mutate({
      numero_factura: values.numero_factura.trim(),
      fecha_factura: values.fecha_factura,
      tipo: values.tipo,
      valor_facturado: values.tipo === "PARCIAL" ? Number(values.valor_facturado) : undefined,
    });
  });

  return (
    <Modal
      open={open}
      onClose={() => {
        setError(null);
        reset();
        onClose();
      }}
      title="Facturar remisión"
      footer={
        <>
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" form="facturar-form" variant="primary" loading={mutation.isPending}>
            Facturar
          </Button>
        </>
      }
    >
      <form
        id="facturar-form"
        onSubmit={onSubmit}
        className={styles.form}
        noValidate
        onClick={(event) => event.stopPropagation()}
      >
        {error && <div className={styles.formError}>{error}</div>}

        <Input
          label="Número de factura"
          placeholder="Ej: F-7-468"
          hint="Formato: una letra mayúscula, guion, dígitos (ej. F-1234 o F-7-468)."
          error={errors.numero_factura?.message}
          {...register("numero_factura", { required: "El número de factura es obligatorio." })}
        />
        <Controller
          control={control}
          name="fecha_factura"
          rules={{ required: "La fecha es obligatoria." }}
          render={({ field }) => (
            <InputFecha
              label="Fecha de factura"
              required
              error={errors.fecha_factura?.message}
              value={field.value}
              onChange={field.onChange}
              onBlur={field.onBlur}
              ref={field.ref}
            />
          )}
        />
        <Select label="Tipo" {...register("tipo")}>
          <option value="TOTAL">Total</option>
          <option value="PARCIAL">Parcial</option>
        </Select>

        {tipo === "PARCIAL" && (
          <Controller
            control={control}
            name="valor_facturado"
            rules={{
              required: "El valor es obligatorio cuando el tipo es Parcial.",
              validate: (v) => Number(v) > 0 || "El valor debe ser mayor que cero.",
            }}
            render={({ field }) => (
              <InputNumero
                label="Valor a facturar"
                moneda
                hint={`Saldo pendiente: ${formatCOP(saldoPendiente)}`}
                error={errors.valor_facturado?.message}
                value={field.value ?? ""}
                onChange={field.onChange}
                onBlur={field.onBlur}
                name={field.name}
              />
            )}
          />
        )}
      </form>
    </Modal>
  );
}
