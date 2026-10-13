import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Search } from "lucide-react";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { getApiErrorMessage } from "../../api/errors";
import {
  asociarTipoATercero,
  createTercero,
  desasociarTipoDeTercero,
  listTerceros,
  listTiposTercero,
  updateTercero,
  type Tercero,
} from "../../api/terceros";
import {
  AsyncSelect,
  Badge,
  Button,
  Checkbox,
  EmptyState,
  FilterPanel,
  Input,
  Modal,
  PageHeader,
  Select,
  Switch,
  Table,
  type TableColumn,
  useToast,
} from "../../components/ui";
import { canWrite } from "../../lib/permissions";
import { useAuthStore } from "../../store/authStore";
import { usePageTitle } from "../../store/pageTitleStore";
import styles from "../../components/CatalogoCRUD.module.css";

const READ_ONLY_TITLE = "No tienes permiso para esta acción (rol Solo Consulta)";
const NOMBRE_TIPO_CONDUCTOR = "conductor";

interface TerceroFormValues {
  identificacion: string;
  nombre: string;
  direccion: string;
  municipio_id: number | null;
  email: string;
  telefono: string;
  regimen: string;
  tiposSeleccionados: number[];
  tiene_licencia: boolean;
  fecha_vencimiento_licencia: string;
}

const DEFAULT_VALUES: TerceroFormValues = {
  identificacion: "",
  nombre: "",
  direccion: "",
  municipio_id: null,
  email: "",
  telefono: "",
  regimen: "",
  tiposSeleccionados: [],
  tiene_licencia: false,
  fecha_vencimiento_licencia: "",
};

export function ListadoTerceros() {
  usePageTitle("Terceros");
  const user = useAuthStore((state) => state.user);
  const puedeEscribir = canWrite(user);
  const toast = useToast();
  const queryClient = useQueryClient();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [tipoFiltro, setTipoFiltro] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<Tercero | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const { data: tiposTercero } = useQuery({
    queryKey: ["tipos-tercero-lookup"],
    queryFn: listTiposTercero,
  });

  const queryKey = ["terceros", page, search, tipoFiltro];
  const { data, isLoading } = useQuery({
    queryKey,
    queryFn: () => listTerceros({ page, q: search || undefined, tipo: tipoFiltro || undefined }),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["terceros"] });

  const {
    control,
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<TerceroFormValues>({ defaultValues: DEFAULT_VALUES });

  const tiposSeleccionados = watch("tiposSeleccionados");
  const esConductor = tiposTercero
    ?.filter((t) => tiposSeleccionados?.includes(t.id))
    .some((t) => t.nombre.toLowerCase() === NOMBRE_TIPO_CONDUCTOR);
  const tieneLicencia = watch("tiene_licencia");

  const openCreateForm = () => {
    setEditingItem(null);
    setFormError(null);
    reset(DEFAULT_VALUES);
    setFormOpen(true);
  };

  const openEditForm = (item: Tercero) => {
    setEditingItem(item);
    setFormError(null);
    reset({
      identificacion: item.identificacion,
      nombre: item.nombre,
      direccion: item.direccion,
      municipio_id: item.municipio_id,
      email: item.email,
      telefono: item.telefono,
      regimen: item.regimen,
      tiposSeleccionados: (tiposTercero ?? [])
        .filter((t) => item.tipos.includes(t.nombre))
        .map((t) => t.id),
      tiene_licencia: item.tiene_licencia ?? false,
      fecha_vencimiento_licencia: item.fecha_vencimiento_licencia ?? "",
    });
    setFormOpen(true);
  };

  const sincronizarTipos = async (terceroId: number, tipoIdsSeleccionados: number[]) => {
    const idsOriginales = editingItem
      ? (tiposTercero ?? []).filter((t) => editingItem.tipos.includes(t.nombre)).map((t) => t.id)
      : [];
    const aAsociar = tipoIdsSeleccionados.filter((id) => !idsOriginales.includes(id));
    const aDesasociar = idsOriginales.filter((id) => !tipoIdsSeleccionados.includes(id));
    await Promise.all([
      ...aAsociar.map((tipoId) => asociarTipoATercero(terceroId, tipoId)),
      ...aDesasociar.map((tipoId) => desasociarTipoDeTercero(terceroId, tipoId)),
    ]);
  };

  const submitMutation = useMutation({
    mutationFn: async (values: TerceroFormValues) => {
      const payload = {
        identificacion: values.identificacion,
        nombre: values.nombre,
        direccion: values.direccion,
        municipio_id: values.municipio_id,
        email: values.email,
        telefono: values.telefono,
        regimen: values.regimen,
        tiene_licencia: esConductor ? values.tiene_licencia : null,
        fecha_vencimiento_licencia: esConductor && values.tiene_licencia ? values.fecha_vencimiento_licencia || null : null,
      };
      const tercero = editingItem
        ? await updateTercero(editingItem.id, payload)
        : await createTercero(payload);
      await sincronizarTipos(tercero.id, values.tiposSeleccionados);
      return tercero;
    },
    onSuccess: (tercero) => {
      invalidate();
      setFormOpen(false);
      toast.success(`Tercero '${tercero.nombre}' guardado correctamente.`);
    },
    onError: (error) => setFormError(getApiErrorMessage(error, "No se pudo guardar el tercero.")),
  });

  const onSubmit = handleSubmit((values) => {
    setFormError(null);
    if (!values.municipio_id) {
      setFormError("Selecciona un municipio.");
      return;
    }
    submitMutation.mutate(values);
  });

  const columns: TableColumn<Tercero>[] = [
    { key: "identificacion", header: "Identificación", monoData: true, render: (t) => t.identificacion },
    { key: "nombre", header: "Nombre", truncate: true, render: (t) => t.nombre },
    {
      key: "tipos",
      header: "Tipos",
      render: (t) => (
        <div style={{ display: "flex", gap: "var(--space-1)", flexWrap: "nowrap" }}>
          {t.tipos.length === 0 ? (
            "—"
          ) : (
            t.tipos.map((tipo) => (
              <Badge key={tipo} variant="accent">
                {tipo.charAt(0).toUpperCase() + tipo.slice(1)}
              </Badge>
            ))
          )}
        </div>
      ),
    },
    { key: "telefono", header: "Teléfono", monoData: true, render: (t) => t.telefono },
    { key: "municipio", header: "Municipio", render: (t) => t.municipio_nombre ?? "—" },
    {
      key: "acciones",
      header: "",
      align: "right",
      render: (row) => (
        <button
          type="button"
          onClick={() => openEditForm(row)}
          disabled={!puedeEscribir}
          title={puedeEscribir ? "Editar" : READ_ONLY_TITLE}
          aria-label="Editar"
          style={actionButtonStyle}
        >
          <Pencil size={16} />
        </button>
      ),
    },
  ];

  const items = data?.items ?? [];
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <PageHeader
      title="Terceros"
      breadcrumb={["Datos", "Terceros"]}
      subtitle="Clientes, conductores, proveedores y demás terceros del sistema."
      actions={
        <Button
          variant="primary"
          leftIcon={<Plus size={16} />}
          onClick={openCreateForm}
          disabled={!puedeEscribir}
          title={puedeEscribir ? undefined : READ_ONLY_TITLE}
        >
          Nuevo tercero
        </Button>
      }
    >
      <FilterPanel
        search={
          <Input
            aria-label="Buscar terceros"
            placeholder="Buscar por nombre o identificación…"
            leftElement={<Search size={18} aria-hidden="true" />}
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        }
        footer={
          <>
            <div style={{ width: 260 }}>
            <Select
              aria-label="Filtrar por tipo"
              value={tipoFiltro}
              onChange={(e) => {
                setTipoFiltro(e.target.value);
                setPage(1);
              }}
            >
              <option value="">Todos los tipos</option>
              {(tiposTercero ?? []).map((t) => (
                <option key={t.id} value={t.nombre}>
                  {t.nombre.charAt(0).toUpperCase() + t.nombre.slice(1)}
                </option>
              ))}
            </Select>
            </div>
            <Button variant="ghost" onClick={() => { setSearch(""); setTipoFiltro(""); setPage(1); }}>
              Limpiar
            </Button>
          </>
        }
      />

      {!isLoading && items.length === 0 ? (
        <EmptyState
          icon={<Search size={32} strokeWidth={1.5} />}
          title="Sin resultados en terceros"
          description="No encontramos registros que coincidan con tu búsqueda."
          action={
            <Button variant="primary" onClick={openCreateForm} disabled={!puedeEscribir}>
              Nuevo tercero
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
              <Button variant="ghost" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>
                Siguiente
              </Button>
            </div>
          )}
        </>
      )}

      <Modal
        open={formOpen}
        onClose={() => setFormOpen(false)}
        title={editingItem ? "Editar tercero" : "Nuevo tercero"}
        footer={
          <>
            <Button type="button" variant="ghost" onClick={() => setFormOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" form="tercero-form" variant="primary" loading={submitMutation.isPending}>
              Guardar
            </Button>
          </>
        }
      >
        <form id="tercero-form" onSubmit={onSubmit} className={styles.form} noValidate>
          {formError && <div className={styles.formError}>{formError}</div>}

          <Input
            label="Identificación"
            monoData
            error={errors.identificacion?.message}
            {...register("identificacion", { required: "La identificación es obligatoria." })}
          />
          <Input
            label="Nombre"
            error={errors.nombre?.message}
            {...register("nombre", { required: "El nombre es obligatorio." })}
          />
          <Input
            label="Dirección"
            error={errors.direccion?.message}
            {...register("direccion", { required: "La dirección es obligatoria." })}
          />
          <Controller
            control={control}
            name="municipio_id"
            render={({ field }) => (
              <AsyncSelect
                label="Municipio"
                endpoint="/api/ubicaciones/municipios"
                getLabel={(item) => String(item.nombre)}
                value={field.value}
                onChange={field.onChange}
                required
              />
            )}
          />
          <Input
            label="Email"
            type="email"
            error={errors.email?.message}
            {...register("email", { required: "El email es obligatorio." })}
          />
          <Input
            label="Teléfono"
            monoData
            error={errors.telefono?.message}
            {...register("telefono", { required: "El teléfono es obligatorio." })}
          />
          <Input
            label="Régimen"
            error={errors.regimen?.message}
            {...register("regimen", { required: "El régimen es obligatorio." })}
          />

          <div>
            <label style={{ display: "block", marginBottom: "var(--space-1)", fontSize: "var(--text-body)", color: "var(--text-secondary)" }}>
              Tipos
            </label>
            <div style={{ display: "flex", gap: "var(--space-4)", flexWrap: "wrap" }}>
              {(tiposTercero ?? []).map((tipo) => (
                <Controller
                  key={tipo.id}
                  control={control}
                  name="tiposSeleccionados"
                  render={({ field }) => (
                    <Checkbox
                      label={tipo.nombre.charAt(0).toUpperCase() + tipo.nombre.slice(1)}
                      checked={field.value.includes(tipo.id)}
                      onChange={(event) => {
                        if (event.target.checked) {
                          field.onChange([...field.value, tipo.id]);
                        } else {
                          field.onChange(field.value.filter((id) => id !== tipo.id));
                        }
                      }}
                    />
                  )}
                />
              ))}
            </div>
          </div>

          {esConductor && (
            <>
              <Controller
                control={control}
                name="tiene_licencia"
                render={({ field }) => (
                  <Switch
                    label="¿Tiene licencia?"
                    checked={field.value}
                    onChange={(event) => field.onChange(event.target.checked)}
                  />
                )}
              />
              {tieneLicencia && (
                <Input
                  label="Fecha de vencimiento de la licencia"
                  type="date"
                  {...register("fecha_vencimiento_licencia")}
                />
              )}
            </>
          )}

        </form>
      </Modal>
    </PageHeader>
  );
}

const actionButtonStyle = {
  background: "transparent",
  border: "none",
  color: "var(--text-secondary)",
  cursor: "pointer",
  padding: "6px",
  borderRadius: "var(--radius-sm)",
  display: "inline-flex",
} as const;
