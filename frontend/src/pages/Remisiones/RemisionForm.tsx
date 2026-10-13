import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  Calendar,
  Clock,
  CreditCard,
  FileText,
  Gauge,
  MapPin,
  Package,
  Printer,
  Receipt,
  Route,
  Tag,
  Truck,
  User,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { useNavigate, useParams } from "react-router-dom";
import { apiClient } from "../../api/client";
import { getApiErrorMessage } from "../../api/errors";
import { createRemision, getRemision, updateRemision } from "../../api/remisiones";
import { formatMoney } from "../../lib/format";
import { AsyncSelect, Button, Input, PageHeader, TabsBar, useToast, type TabItem } from "../../components/ui";
import { canWrite } from "../../lib/permissions";
import { useAuthStore } from "../../store/authStore";
import { usePageTitle } from "../../store/pageTitleStore";
import { FacturacionPanel } from "./FacturacionPanel";
import { ProductosSection } from "./ProductosSection";
import styles from "../../components/CatalogoCRUD.module.css";
import formStyles from "./RemisionForm.module.css";

const NOMBRE_TIPO_SERVICIO_CAMABAJA = "Cama baja";

type TabKey = "datos" | "productos" | "facturacion";

interface RemisionFormValues {
  prefijo_id: number | null;
  orden_servicio_id: number | null;
  numero_remision: string;
  fecha: string;
  forma_pago_id: number | null;
  cliente_id: number | null;
  conductor_id: number | null;
  origen_municipio_id: number | null;
  destino_municipio_id: number | null;
  proyecto_id: number | null;
  tramo_id: number | null;
  tipo_servicio_id: number | null;
  vehiculo_id: number | null;
  camabaja_id: number | null;
  kilometros: string;
  hora_salida: string;
  hora_llegada: string;
  remision_agresur: string;
  observaciones: string;
}

const DEFAULT_VALUES: RemisionFormValues = {
  prefijo_id: null,
  orden_servicio_id: null,
  numero_remision: "",
  fecha: new Date().toISOString().slice(0, 10),
  forma_pago_id: null,
  cliente_id: null,
  conductor_id: null,
  origen_municipio_id: null,
  destino_municipio_id: null,
  proyecto_id: null,
  tramo_id: null,
  tipo_servicio_id: null,
  vehiculo_id: null,
  camabaja_id: null,
  kilometros: "",
  hora_salida: "",
  hora_llegada: "",
  remision_agresur: "",
  observaciones: "",
};

export function RemisionForm() {
  const params = useParams<{ id: string }>();
  const isEditing = params.id !== undefined && params.id !== "nueva";
  const remisionId = isEditing ? Number(params.id) : null;

  usePageTitle(isEditing ? "Editar remisión" : "Nueva remisión");
  const navigate = useNavigate();
  const toast = useToast();
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);
  const puedeEscribir = canWrite(user);

  const [serverError, setServerError] = useState<string | null>(null);
  const [tab, setTab] = useState<TabKey>("datos");

  const { data: remision, isLoading: cargandoRemision, isError: errorRemision } = useQuery({
    queryKey: ["remision", remisionId],
    queryFn: () => getRemision(remisionId as number),
    enabled: remisionId != null,
  });

  const { data: prefijos } = useQuery({
    queryKey: ["prefijos-lookup"],
    queryFn: async () => {
      const { data } = await apiClient.get("/api/catalogos/prefijos", { params: { page_size: 100 } });
      return data.items as { id: number; codigo: string; es_manual: boolean }[];
    },
  });

  const { data: tiposServicio } = useQuery({
    queryKey: ["tipos-servicio-lookup"],
    queryFn: async () => {
      const { data } = await apiClient.get("/api/catalogos/tipos_servicio", { params: { page_size: 100 } });
      return data.items as { id: number; nombre: string }[];
    },
  });

  const {
    control,
    register,
    handleSubmit,
    watch,
    reset,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<RemisionFormValues>({ defaultValues: DEFAULT_VALUES });

  useEffect(() => {
    if (!remision) return;
    reset({
      prefijo_id: remision.prefijo_id,
      orden_servicio_id: remision.orden_servicio_id,
      numero_remision: remision.numero_remision,
      fecha: remision.fecha,
      forma_pago_id: remision.forma_pago_id,
      cliente_id: remision.cliente_id,
      conductor_id: remision.conductor_id,
      origen_municipio_id: remision.origen_municipio_id,
      destino_municipio_id: remision.destino_municipio_id,
      proyecto_id: remision.proyecto_id,
      tramo_id: remision.tramo_id,
      tipo_servicio_id: remision.tipo_servicio_id,
      vehiculo_id: remision.vehiculo_id,
      camabaja_id: remision.camabaja_id,
      kilometros: remision.kilometros ?? "",
      hora_salida: remision.hora_salida ?? "",
      hora_llegada: remision.hora_llegada ?? "",
      remision_agresur: remision.remision_agresur ?? "",
      observaciones: remision.observaciones ?? "",
    });
  }, [remision, reset]);

  const prefijoSeleccionado = prefijos?.find((p) => p.id === watch("prefijo_id"));
  const tipoServicioCamabaja = tiposServicio?.find((t) => t.nombre === NOMBRE_TIPO_SERVICIO_CAMABAJA);
  const esCamabaja = tipoServicioCamabaja != null && watch("tipo_servicio_id") === tipoServicioCamabaja.id;
  const proyectoId = watch("proyecto_id");

  const bloqueada = remision?.estado_facturacion === "FACTURADA";

  const crearMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => createRemision(payload),
    onSuccess: (nueva) => {
      queryClient.invalidateQueries({ queryKey: ["remisiones"] });
      toast.success(`Remisión ${nueva.numero_remision} creada correctamente.`);
      navigate(`/remisiones/${nueva.id}`, { replace: true });
    },
    onError: (error) => setServerError(getApiErrorMessage(error, "No se pudo crear la remisión.")),
  });

  const actualizarMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => updateRemision(remisionId as number, payload),
    onSuccess: ({ remision: actualizada, advertencia }) => {
      queryClient.invalidateQueries({ queryKey: ["remisiones"] });
      queryClient.invalidateQueries({ queryKey: ["remision", remisionId] });
      toast.success(`Remisión ${actualizada.numero_remision} actualizada correctamente.`);
      if (advertencia) toast.error(advertencia);
    },
    onError: (error) => setServerError(getApiErrorMessage(error, "No se pudo actualizar la remisión.")),
  });

  const onSubmit = handleSubmit((values) => {
    setServerError(null);

    if (prefijoSeleccionado?.es_manual && !values.numero_remision.trim()) {
      setServerError(
        `El prefijo '${prefijoSeleccionado.codigo}' es manual (remisión de papel): número de remisión es obligatorio.`,
      );
      return;
    }
    if (esCamabaja && !values.camabaja_id) {
      setServerError("El tipo de servicio 'Cama baja' requiere especificar el activo de cama baja.");
      return;
    }
    if (!esCamabaja && values.camabaja_id) {
      setServerError("El campo de cama baja solo aplica cuando el tipo de servicio es 'Cama baja'.");
      return;
    }
    if (!values.cliente_id || !values.origen_municipio_id || !values.destino_municipio_id || !values.prefijo_id) {
      setServerError("Completa los campos obligatorios: prefijo, cliente, origen y destino.");
      return;
    }

    const basePayload: Record<string, unknown> = {
      fecha: values.fecha,
      orden_servicio_id: values.orden_servicio_id,
      forma_pago_id: values.forma_pago_id,
      cliente_id: values.cliente_id,
      conductor_id: values.conductor_id,
      origen_municipio_id: values.origen_municipio_id,
      destino_municipio_id: values.destino_municipio_id,
      proyecto_id: values.proyecto_id,
      tramo_id: values.tramo_id,
      tipo_servicio_id: values.tipo_servicio_id,
      vehiculo_id: values.vehiculo_id,
      camabaja_id: esCamabaja ? values.camabaja_id : null,
      kilometros: values.kilometros === "" ? null : Number(values.kilometros),
      hora_salida: values.hora_salida || null,
      hora_llegada: values.hora_llegada || null,
      remision_agresur: values.remision_agresur.trim() || null,
      observaciones: values.observaciones || null,
    };

    if (isEditing) {
      actualizarMutation.mutate(basePayload);
    } else {
      crearMutation.mutate({
        ...basePayload,
        prefijo_id: values.prefijo_id,
        numero_remision: values.numero_remision || undefined,
      });
    }
  });

  if (isEditing && cargandoRemision) {
    return <p>Cargando remisión…</p>;
  }

  if (isEditing && (errorRemision || (!cargandoRemision && !remision))) {
    return (
      <div className={formStyles.page}>
        <PageHeader title="Remisión no encontrada" breadcrumb={["Operación", "Remisiones"]} />
        <div className={styles.formError} style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", flexWrap: "wrap" }}>
          <AlertTriangle size={18} />
          <span>No encontramos esta remisión. Puede que haya sido eliminada o que el enlace esté incompleto.</span>
          <Button type="button" variant="secondary" onClick={() => navigate("/remisiones")}>
            Volver a remisiones
          </Button>
        </div>
      </div>
    );
  }

  const productosCount = remision?.productos.length ?? 0;
  const tabs: TabItem<TabKey>[] = [
    { key: "datos", label: "Datos", icon: <FileText size={16} /> },
    {
      key: "productos",
      label: "Productos",
      icon: <Package size={16} />,
      count: productosCount,
      disabled: !isEditing,
      disabledHint: "Guarda la remisión para agregar productos.",
    },
    {
      key: "facturacion",
      label: "Facturación",
      icon: <Receipt size={16} />,
      disabled: !isEditing,
      disabledHint: "Guarda la remisión para facturarla.",
    },
  ];

  const breadcrumb = ["Operación", "Remisiones", isEditing ? `Remisión ${remision?.numero_remision ?? ""}`.trim() : "Nueva"];

  return (
    <div className={formStyles.page}>
      <PageHeader
        title={isEditing ? "Editar remisión" : "Nueva remisión"}
        breadcrumb={breadcrumb}
        actions={
          <>
            {isEditing && (
              <Button
                type="button"
                variant="ghost"
                leftIcon={<Printer size={16} />}
                onClick={() => window.open(`/remisiones/${remisionId}/imprimir`, "_blank")}
              >
                Imprimir
              </Button>
            )}
            {!bloqueada && (
              <Button
                type="submit"
                form="remision-form"
                variant="primary"
                loading={isSubmitting || crearMutation.isPending || actualizarMutation.isPending}
                disabled={!puedeEscribir}
              >
                Guardar remisión
              </Button>
            )}
            <button
              type="button"
              onClick={() => navigate("/remisiones")}
              title={bloqueada ? "Volver a remisiones" : "Cancelar y volver"}
              aria-label={bloqueada ? "Volver a remisiones" : "Cancelar y volver"}
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                width: "36px",
                height: "36px",
                borderRadius: "50%",
                border: "1.5px solid var(--border)",
                background: "transparent",
                color: "var(--text-secondary)",
                cursor: "pointer",
                transition: "background 0.15s, color 0.15s, border-color 0.15s",
                flexShrink: 0,
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLButtonElement).style.background = "var(--danger-bg)";
                (e.currentTarget as HTMLButtonElement).style.color = "var(--danger)";
                (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--danger)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.background = "transparent";
                (e.currentTarget as HTMLButtonElement).style.color = "var(--text-secondary)";
                (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--border)";
              }}
            >
              <X size={18} strokeWidth={2} />
            </button>
          </>
        }
      />

      {bloqueada && (
        <div className={styles.formError} style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-4)" }}>
          <AlertTriangle size={18} />
          Esta remisión está totalmente facturada (FACTURADA) y no se puede editar. Solo puedes consultarla.
        </div>
      )}

      <TabsBar items={tabs} value={tab} onChange={setTab} />

      {tab === "datos" && (
        <form id="remision-form" onSubmit={onSubmit} noValidate className={formStyles.form}>
          {serverError && <div className={styles.formError} style={{ marginBottom: "var(--space-3)" }}>{serverError}</div>}

          <div className={formStyles.grid4}>
            <div className={formStyles.span2}>
              <Controller
                control={control}
                name="cliente_id"
                render={({ field }) => (
                  <AsyncSelect
                    label="Cliente"
                    endpoint="/api/terceros"
                    params={{ tipo: "cliente" }}
                    getLabel={(item) => String(item.nombre)}
                    value={field.value}
                    onChange={field.onChange}
                    disabled={bloqueada}
                    placeholder="Buscar por nombre o NIT"
                    icon={<User size={16} aria-hidden="true" />}
                    required
                  />
                )}
              />
            </div>

            <div>
              <Controller
                control={control}
                name="orden_servicio_id"
                render={({ field }) => (
                  <AsyncSelect
                    label="Número de orden de servicio"
                    endpoint="/api/ordenes-servicio"
                    getLabel={(item) =>
                      `${item.numero} — ${formatMoney(Number(item.saldo_disponible))} disponible`
                    }
                    value={field.value}
                    onChange={field.onChange}
                    disabled={bloqueada}
                    placeholder="Opcional"
                    icon={<FileText size={16} aria-hidden="true" />}
                  />
                )}
              />
              {isEditing && (
                <p className={formStyles.avisoOrden}>
                  Cambiar la orden elimina los productos de esta remisión.
                </p>
              )}
            </div>

            {prefijoSeleccionado?.es_manual ? (
              <Input
                label="Número de remisión (manual)"
                placeholder="Ej: 00123"
                disabled={isEditing || bloqueada}
                error={errors.numero_remision?.message}
                leftElement={<FileText size={16} aria-hidden="true" />}
                {...register("numero_remision")}
              />
            ) : (
              <Input
                label="Número de consecutivo"
                value={isEditing ? remision?.numero_remision ?? "" : "Automático"}
                disabled
                readOnly
                leftElement={<FileText size={16} aria-hidden="true" />}
              />
            )}

            <Controller
              control={control}
              name="prefijo_id"
              render={({ field }) => (
                <AsyncSelect
                  label="Prefijo"
                  endpoint="/api/catalogos/prefijos"
                  getLabel={(item) => `${item.codigo}${item.es_manual ? " (manual)" : ""}`}
                  value={field.value}
                  onChange={field.onChange}
                  disabled={isEditing || bloqueada}
                  placeholder="Seleccionar"
                  icon={<Tag size={16} aria-hidden="true" />}
                  required
                />
              )}
            />

            <Input
              label="Fecha"
              type="date"
              disabled={bloqueada}
              error={errors.fecha?.message}
              leftElement={<Calendar size={16} aria-hidden="true" />}
              {...register("fecha", { required: "La fecha es obligatoria." })}
            />

            <Controller
              control={control}
              name="forma_pago_id"
              render={({ field }) => (
                <AsyncSelect
                  label="Forma de pago"
                  endpoint="/api/catalogos/formas_pago"
                  getLabel={(item) => String(item.nombre)}
                  value={field.value}
                  onChange={field.onChange}
                  disabled={bloqueada}
                  placeholder="Seleccionar"
                  icon={<CreditCard size={16} aria-hidden="true" />}
                />
              )}
            />

            <Controller
              control={control}
              name="tipo_servicio_id"
              render={({ field }) => (
                <AsyncSelect
                  label="Tipo de transporte"
                  endpoint="/api/catalogos/tipos_servicio"
                  getLabel={(item) => String(item.nombre)}
                  value={field.value}
                  onChange={field.onChange}
                  disabled={bloqueada}
                  placeholder="Seleccionar"
                  icon={<Truck size={16} aria-hidden="true" />}
                />
              )}
            />

            <div className={formStyles.span2}>
              <Controller
                control={control}
                name="origen_municipio_id"
                render={({ field }) => (
                  <AsyncSelect
                    label="Ubicación de origen"
                    endpoint="/api/ubicaciones/municipios"
                    getLabel={(item) => String(item.nombre)}
                    value={field.value}
                    onChange={field.onChange}
                    disabled={bloqueada}
                    placeholder="Seleccionar origen"
                    icon={<MapPin size={16} aria-hidden="true" />}
                    required
                  />
                )}
              />
            </div>

            <div className={formStyles.span2}>
              <Controller
                control={control}
                name="destino_municipio_id"
                render={({ field }) => (
                  <AsyncSelect
                    label="Ubicación de destino"
                    endpoint="/api/ubicaciones/municipios"
                    getLabel={(item) => String(item.nombre)}
                    value={field.value}
                    onChange={field.onChange}
                    disabled={bloqueada}
                    placeholder="Seleccionar destino"
                    icon={<MapPin size={16} aria-hidden="true" />}
                    required
                  />
                )}
              />
            </div>

            <Controller
              control={control}
              name="conductor_id"
              render={({ field }) => (
                <AsyncSelect
                  label="Conductor"
                  endpoint="/api/terceros"
                  params={{ tipo: "conductor" }}
                  getLabel={(item) => String(item.nombre)}
                  value={field.value}
                  onChange={field.onChange}
                  disabled={bloqueada}
                  placeholder="Buscar conductor"
                  icon={<User size={16} aria-hidden="true" />}
                />
              )}
            />

            <Controller
              control={control}
              name="vehiculo_id"
              render={({ field }) => (
                <AsyncSelect
                  label="Vehículo"
                  endpoint="/api/activos"
                  params={{ tipo_activo: "Vehículo" }}
                  getLabel={(item) => String(item.placa)}
                  value={field.value}
                  onChange={field.onChange}
                  disabled={bloqueada}
                  placeholder="Buscar por placa"
                  icon={<Truck size={16} aria-hidden="true" />}
                />
              )}
            />

            <Input
              label="Hora de salida"
              type="time"
              disabled={bloqueada}
              leftElement={<Clock size={16} aria-hidden="true" />}
              {...register("hora_salida")}
            />

            <Input
              label="Hora de llegada"
              type="time"
              disabled={bloqueada}
              leftElement={<Clock size={16} aria-hidden="true" />}
              {...register("hora_llegada")}
            />

            <Controller
              control={control}
              name="proyecto_id"
              render={({ field }) => (
                <AsyncSelect
                  label="Proyecto"
                  endpoint="/api/catalogos/proyectos"
                  getLabel={(item) => String(item.nombre)}
                  value={field.value}
                  onChange={(value) => {
                    field.onChange(value);
                    setValue("tramo_id", null);
                  }}
                  disabled={bloqueada}
                  placeholder="Seleccionar"
                  icon={<Route size={16} aria-hidden="true" />}
                />
              )}
            />

            <Controller
              control={control}
              name="tramo_id"
              render={({ field }) => (
                <AsyncSelect
                  label="Tramo"
                  endpoint="/api/catalogos/tramos"
                  params={{ proyecto_id: proyectoId ?? undefined }}
                  getLabel={(item) => String(item.nombre)}
                  value={field.value}
                  onChange={field.onChange}
                  disabled={bloqueada || !proyectoId}
                  placeholder={proyectoId ? "Seleccionar tramo" : "Elige un proyecto"}
                  icon={<Route size={16} aria-hidden="true" />}
                />
              )}
            />

            <Input
              label="Kilómetros"
              type="number"
              step="0.001"
              disabled={bloqueada}
              leftElement={<Gauge size={16} aria-hidden="true" />}
              rightElement={<span style={{ fontSize: 12, color: "var(--text-secondary)" }}>km</span>}
              {...register("kilometros")}
            />

            <Input
              label="Remisión AGRESUR"
              maxLength={30}
              placeholder="Opcional"
              disabled={bloqueada}
              leftElement={<FileText size={16} aria-hidden="true" />}
              {...register("remision_agresur")}
            />

            {esCamabaja && (
              <Controller
                control={control}
                name="camabaja_id"
                render={({ field }) => (
                  <AsyncSelect
                    label="Cama baja / Trailer / Volco"
                    endpoint="/api/activos"
                    params={{ tipo_activo: "Cama baja" }}
                    getLabel={(item) => String(item.placa)}
                    value={field.value}
                    onChange={field.onChange}
                    disabled={bloqueada}
                    placeholder="Buscar por placa"
                    icon={<Truck size={16} aria-hidden="true" />}
                    required
                  />
                )}
              />
            )}

            <div className={formStyles.spanRest}>
              <label className={formStyles.label} htmlFor="remision-observaciones">Observaciones</label>
              <textarea
                id="remision-observaciones"
                rows={2}
                disabled={bloqueada}
                placeholder="Notas que aparecerán en la remisión impresa…"
                className={formStyles.textarea}
                {...register("observaciones")}
              />
            </div>
          </div>
        </form>
      )}

      {tab === "productos" && isEditing && remisionId != null && remision && (
        <ProductosSection remisionId={remisionId} productos={remision.productos} bloqueada={bloqueada} puedeEscribir={puedeEscribir} />
      )}
      {tab === "facturacion" && isEditing && remisionId != null && (
        <FacturacionPanel remisionId={remisionId} puedeEscribir={puedeEscribir} />
      )}
    </div>
  );
}
