import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Lock, Pencil, Plus, Search, Unlock } from "lucide-react";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { getApiErrorMessage } from "../../api/errors";
import {
  alternarBloqueoActivo,
  createActivo,
  listActivos,
  updateActivo,
  type Activo,
} from "../../api/activos";
import {
  AsyncSelect,
  Button,
  Checkbox,
  EmptyState,
  EstadoPunto,
  FilterPanel,
  FormGrid,
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
import { useAuthStore } from "../../store/authStore";
import { usePageTitle } from "../../store/pageTitleStore";
import styles from "../../components/CatalogoCRUD.module.css";

const READ_ONLY_TITLE = "No tienes permiso para esta acción (rol Solo Consulta)";

interface ActivoFormValues {
  placa: string;
  tipo_activo: string;
  clase: string;
  empresa_id: number | null;
  es_segunda_mano: boolean;
}

const DEFAULT_VALUES: ActivoFormValues = {
  placa: "",
  tipo_activo: "",
  clase: "",
  empresa_id: null,
  es_segunda_mano: false,
};

export function ListadoActivos() {
  usePageTitle("Activos");
  const user = useAuthStore((state) => state.user);
  const puedeEscribir = canWrite(user);
  const toast = useToast();
  const queryClient = useQueryClient();

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(() => leerFilasPorPaginaGuardadas("activos", 20));
  const [search, setSearch] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<Activo | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [bloqueoTarget, setBloqueoTarget] = useState<Activo | null>(null);
  const { ordenamiento, alternar: alternarOrden } = useOrdenamiento();

  const queryKey = ["activos", page, pageSize, search, ordenamiento];
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey,
    queryFn: () =>
      listActivos({
        page,
        page_size: pageSize,
        q: search || undefined,
        ordenar_por: ordenamiento.campo ?? undefined,
        sentido: ordenamiento.sentido ?? undefined,
      }),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["activos"] });

  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ActivoFormValues>({ defaultValues: DEFAULT_VALUES });

  const openCreateForm = () => {
    setEditingItem(null);
    setFormError(null);
    reset(DEFAULT_VALUES);
    setFormOpen(true);
  };

  const openEditForm = (item: Activo) => {
    setEditingItem(item);
    setFormError(null);
    reset({
      placa: item.placa,
      tipo_activo: item.tipo_activo,
      clase: item.clase,
      empresa_id: item.empresa_id,
      es_segunda_mano: item.es_segunda_mano,
    });
    setFormOpen(true);
  };

  const submitMutation = useMutation({
    mutationFn: (values: ActivoFormValues) =>
      editingItem ? updateActivo(editingItem.id, { ...values }) : createActivo({ ...values }),
    onSuccess: (activo) => {
      invalidate();
      setFormOpen(false);
      toast.success(`Activo '${activo.placa}' guardado correctamente.`);
    },
    onError: (error) => setFormError(getApiErrorMessage(error, "No se pudo guardar el activo.")),
  });

  const bloqueoMutation = useMutation({
    mutationFn: (id: number) => alternarBloqueoActivo(id),
    onSuccess: (activo) => {
      invalidate();
      toast.success(`Activo '${activo.placa}' ${activo.bloqueado ? "bloqueado" : "desbloqueado"} correctamente.`);
      setBloqueoTarget(null);
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "No se pudo cambiar el estado del activo."));
      setBloqueoTarget(null);
    },
  });

  const onSubmit = handleSubmit((values) => {
    setFormError(null);
    if (!values.empresa_id) {
      setFormError("Selecciona una empresa.");
      return;
    }
    submitMutation.mutate(values);
  });

  const columns: TableColumn<Activo>[] = [
    { key: "placa", header: "Placa", monoData: true, sortField: "placa", render: (a) => a.placa },
    { key: "tipo_activo", header: "Tipo", sortField: "tipo_activo", render: (a) => a.tipo_activo },
    { key: "clase", header: "Clase", sortField: "clase", render: (a) => a.clase },
    { key: "empresa", header: "Empresa", render: (a) => a.empresa_nombre ?? "—" },
    {
      key: "estado",
      header: "Estado",
      sortField: "bloqueado",
      render: (a) => <EstadoPunto color={a.bloqueado ? "danger" : "success"}>{a.bloqueado ? "Bloqueado" : "Activo"}</EstadoPunto>,
    },
    {
      key: "acciones",
      header: "",
      align: "right",
      render: (row) => (
        <div style={{ display: "flex", gap: "var(--space-1)", justifyContent: "flex-end" }}>
          <IconButton
            label={puedeEscribir ? "Editar" : READ_ONLY_TITLE}
            icon={<Pencil size={16} />}
            onClick={() => openEditForm(row)}
            disabled={!puedeEscribir}
          />
          <IconButton
            label={puedeEscribir ? (row.bloqueado ? "Desbloquear" : "Bloquear") : READ_ONLY_TITLE}
            icon={row.bloqueado ? <Unlock size={16} /> : <Lock size={16} />}
            onClick={() => setBloqueoTarget(row)}
            disabled={!puedeEscribir}
          />
        </div>
      ),
    },
  ];

  const items = data?.items ?? [];
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <PageHeader
      title="Activos"
      breadcrumb={["Datos", "Activos"]}
      actions={
        <Button
          variant="primary"
          leftIcon={<Plus size={16} />}
          onClick={openCreateForm}
          disabled={!puedeEscribir}
          title={puedeEscribir ? undefined : READ_ONLY_TITLE}
        >
          Nuevo activo
        </Button>
      }
    >
      <FilterPanel
        search={
          <Input
            placeholder="Buscar por placa…"
            leftElement={<Search size={16} aria-hidden="true" />}
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            aria-label="Buscar"
          />
        }
      />

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
          title="Sin resultados en activos"
          description={search ? "No encontramos registros que coincidan con tu búsqueda." : "Todavía no hay ningún activo."}
          action={
            !search && (
              <Button variant="primary" onClick={openCreateForm} disabled={!puedeEscribir}>
                Nuevo activo
              </Button>
            )
          }
        />
      ) : (
        <>
          <Table
            columns={columns}
            data={items}
            getRowId={(row) => row.id}
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
                  guardarFilasPorPagina("activos", n);
                  setPage(1);
                }}
              />
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
        title={editingItem ? "Editar activo" : "Nuevo activo"}
        footer={
          <>
            <Button type="button" variant="ghost" onClick={() => setFormOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" form="activo-form" variant="primary" loading={submitMutation.isPending}>
              Guardar
            </Button>
          </>
        }
      >
        <form id="activo-form" onSubmit={onSubmit} className={styles.form} noValidate>
          {formError && <div className={styles.formError}>{formError}</div>}

          <FormGrid columns={2}>
            <Input
              label="Placa"
              required
              monoData
              error={errors.placa?.message}
              {...register("placa", { required: "La placa es obligatoria." })}
            />
            <Input
              label="Tipo de activo"
              required
              placeholder="Ej: Vehículo, Cama baja"
              error={errors.tipo_activo?.message}
              {...register("tipo_activo", { required: "El tipo de activo es obligatorio." })}
            />
            <Input
              label="Clase"
              required
              placeholder="Ej: Tractocamión, Volqueta"
              error={errors.clase?.message}
              {...register("clase", { required: "La clase es obligatoria." })}
            />
            <Controller
              control={control}
              name="empresa_id"
              render={({ field }) => (
                <AsyncSelect
                  label="Empresa"
                  endpoint="/api/empresas"
                  getLabel={(item) => String(item.nombre)}
                  value={field.value}
                  onChange={field.onChange}
                  required
                />
              )}
            />
          </FormGrid>
          <Controller
            control={control}
            name="es_segunda_mano"
            render={({ field }) => (
              <Checkbox
                label="¿Es de segunda mano?"
                checked={field.value}
                onChange={(event) => field.onChange(event.target.checked)}
              />
            )}
          />
        </form>
      </Modal>

      <Modal
        open={Boolean(bloqueoTarget)}
        onClose={() => setBloqueoTarget(null)}
        title={bloqueoTarget?.bloqueado ? "Confirmar desbloqueo" : "Confirmar bloqueo"}
        size="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setBloqueoTarget(null)}>
              Cancelar
            </Button>
            <Button
              variant={bloqueoTarget?.bloqueado ? "primary" : "danger"}
              loading={bloqueoMutation.isPending}
              onClick={() => bloqueoTarget && bloqueoMutation.mutate(bloqueoTarget.id)}
            >
              {bloqueoTarget?.bloqueado ? "Desbloquear" : "Bloquear"}
            </Button>
          </>
        }
      >
        <p className={styles.confirmText}>
          ¿Seguro que quieres {bloqueoTarget?.bloqueado ? "desbloquear" : "bloquear"} el activo{" "}
          <strong className="font-mono-data">{bloqueoTarget?.placa}</strong>?
        </p>
      </Modal>
    </PageHeader>
  );
}
