import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { KeyRound, Pencil, Plus, Search } from "lucide-react";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { getApiErrorMessage } from "../../api/errors";
import {
  asignarRolAUsuario,
  createUsuario,
  listRoles,
  listUsuarios,
  quitarRolDeUsuario,
  updateUsuario,
  type UsuarioAdmin,
} from "../../api/admin";
import {
  Badge,
  Button,
  Checkbox,
  EmptyState,
  EstadoPunto,
  FilterPanel,
  IconButton,
  Input,
  Modal,
  PageHeader,
  SelectorFilasPorPagina,
  Switch,
  Table,
  type TableColumn,
  guardarFilasPorPagina,
  leerFilasPorPaginaGuardadas,
  rangoRegistros,
  useToast,
} from "../../components/ui";
import { useOrdenamiento } from "../../hooks/useOrdenamiento";
import { useAuthStore } from "../../store/authStore";
import { usePageTitle } from "../../store/pageTitleStore";
import styles from "../../components/CatalogoCRUD.module.css";

const PERMISO_ADMIN = "usuarios.administrar";

interface UsuarioFormValues {
  nombre: string;
  email: string;
  identificacion: string;
  password: string;
  activo: boolean;
  rolesSeleccionados: number[];
}

const DEFAULT_VALUES: UsuarioFormValues = {
  nombre: "",
  email: "",
  identificacion: "",
  password: "",
  activo: true,
  rolesSeleccionados: [],
};

export function Usuarios() {
  usePageTitle("Usuarios");
  const currentUser = useAuthStore((state) => state.user);
  const toast = useToast();
  const queryClient = useQueryClient();

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(() => leerFilasPorPaginaGuardadas("usuarios", 20));
  const [search, setSearch] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<UsuarioAdmin | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [passwordTarget, setPasswordTarget] = useState<UsuarioAdmin | null>(null);
  const { ordenamiento, alternar: alternarOrden } = useOrdenamiento();

  const { data: roles } = useQuery({
    queryKey: ["roles-lookup"],
    queryFn: async () => (await listRoles(1, "")).items,
  });

  const queryKey = ["usuarios-admin", page, pageSize, search, ordenamiento];
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey,
    queryFn: () => listUsuarios(page, search, pageSize, ordenamiento.campo ?? undefined, ordenamiento.sentido ?? undefined),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["usuarios-admin"] });

  const {
    control,
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<UsuarioFormValues>({ defaultValues: DEFAULT_VALUES });

  const rolesSeleccionados = watch("rolesSeleccionados");

  const rolesConPermisoAdmin = (roles ?? []).filter((r) => r.permisos.includes(PERMISO_ADMIN)).map((r) => r.id);
  const esUsuarioActual = editingItem != null && currentUser != null && editingItem.id === currentUser.id;
  const perderiaAccesoAdmin =
    esUsuarioActual && !rolesSeleccionados?.some((id) => rolesConPermisoAdmin.includes(id));

  const openCreateForm = () => {
    setEditingItem(null);
    setFormError(null);
    reset(DEFAULT_VALUES);
    setFormOpen(true);
  };

  const openEditForm = (item: UsuarioAdmin) => {
    setEditingItem(item);
    setFormError(null);
    reset({
      nombre: item.nombre,
      email: item.email,
      identificacion: item.identificacion ?? "",
      password: "",
      activo: item.activo,
      rolesSeleccionados: (roles ?? []).filter((r) => item.roles.includes(r.nombre)).map((r) => r.id),
    });
    setFormOpen(true);
  };

  const sincronizarRoles = async (usuarioId: number, rolIdsSeleccionados: number[]) => {
    const idsOriginales = editingItem
      ? (roles ?? []).filter((r) => editingItem.roles.includes(r.nombre)).map((r) => r.id)
      : [];
    const aAsignar = rolIdsSeleccionados.filter((id) => !idsOriginales.includes(id));
    const aQuitar = idsOriginales.filter((id) => !rolIdsSeleccionados.includes(id));
    await Promise.all([
      ...aAsignar.map((rolId) => asignarRolAUsuario(usuarioId, rolId)),
      ...aQuitar.map((rolId) => quitarRolDeUsuario(usuarioId, rolId)),
    ]);
  };

  const submitMutation = useMutation({
    mutationFn: async (values: UsuarioFormValues) => {
      const payload: Record<string, unknown> = {
        nombre: values.nombre.trim().toUpperCase(),
        email: values.email.trim().toLowerCase(),
        identificacion: values.identificacion.trim() || null,
        activo: values.activo,
      };
      if (!editingItem) payload.password = values.password;
      const usuario = editingItem ? await updateUsuario(editingItem.id, payload) : await createUsuario(payload);
      await sincronizarRoles(usuario.id, values.rolesSeleccionados);
      return usuario;
    },
    onSuccess: (usuario) => {
      invalidate();
      setFormOpen(false);
      toast.success(`Usuario '${usuario.nombre}' guardado correctamente.`);
    },
    onError: (error) => setFormError(getApiErrorMessage(error, "No se pudo guardar el usuario.")),
  });

  const onSubmit = handleSubmit((values) => {
    setFormError(null);
    if (perderiaAccesoAdmin) {
      setFormError(
        "No puedes quitarte a ti mismo todos los roles que otorgan el permiso 'usuarios.administrar': te quedarías sin acceso a esta sección.",
      );
      return;
    }
    submitMutation.mutate(values);
  });

  const columns: TableColumn<UsuarioAdmin>[] = [
    { key: "nombre", header: "Nombre", sortField: "nombre", render: (u) => u.nombre },
    { key: "email", header: "Email", monoData: true, sortField: "email", render: (u) => u.email },
    {
      key: "roles", sortField: "roles",
      header: "Roles",
      render: (u) => (
        <div style={{ display: "flex", gap: "var(--space-1)", flexWrap: "wrap" }}>
          {u.roles.length === 0 ? "—" : u.roles.map((rol) => <Badge key={rol} variant="accent">{rol}</Badge>)}
        </div>
      ),
    },
    {
      key: "estado",
      header: "Estado",
      sortField: "activo",
      render: (u) => <EstadoPunto color={u.activo ? "success" : "danger"}>{u.activo ? "Activo" : "Inactivo"}</EstadoPunto>,
    },
    {
      key: "acciones",
      header: "",
      align: "right",
      render: (row) => (
        <div style={{ display: "flex", gap: "var(--space-1)", justifyContent: "flex-end" }}>
          <IconButton label="Editar" icon={<Pencil size={16} />} onClick={() => openEditForm(row)} />
          <IconButton label="Cambiar contraseña" icon={<KeyRound size={16} />} onClick={() => setPasswordTarget(row)} />
        </div>
      ),
    },
  ];

  const items = data?.items ?? [];
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <PageHeader
      title="Usuarios"
      breadcrumb={["Análisis", "Administración"]}
      actions={
        <Button variant="primary" leftIcon={<Plus size={16} />} onClick={openCreateForm}>
          Nuevo usuario
        </Button>
      }
    >
      <FilterPanel
        search={
          <Input
            placeholder="Buscar por nombre o email…"
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
          title="Sin resultados en usuarios"
          description="No encontramos registros que coincidan con tu búsqueda."
          action={
            <Button variant="primary" onClick={openCreateForm}>
              Nuevo usuario
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
                  guardarFilasPorPagina("usuarios", n);
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
        title={editingItem ? "Editar usuario" : "Nuevo usuario"}
        footer={
          <>
            <Button type="button" variant="ghost" onClick={() => setFormOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" form="usuario-form" variant="primary" loading={submitMutation.isPending} disabled={perderiaAccesoAdmin}>
              Guardar
            </Button>
          </>
        }
      >
        <form id="usuario-form" onSubmit={onSubmit} className={styles.form} noValidate>
          {formError && <div className={styles.formError}>{formError}</div>}

          <Input
            label="Nombre"
            style={{ textTransform: "uppercase" }}
            error={errors.nombre?.message}
            {...register("nombre", { required: "El nombre es obligatorio." })}
          />
          <Input
            label="Email"
            type="email"
            error={errors.email?.message}
            {...register("email", { required: "El email es obligatorio." })}
          />
          <Input
            label="Identificación (cédula)"
            monoData
            inputMode="text"
            placeholder="Opcional"
            hint="Sale en los reportes como «ID del usuario». Si se deja vacía, esa columna queda vacía."
            error={errors.identificacion?.message}
            {...register("identificacion", {
              maxLength: { value: 30, message: "Máximo 30 caracteres." },
              pattern: {
                value: /^\s*[0-9A-Za-z.-]*\s*$/,
                message: "Solo números, letras, punto o guion.",
              },
            })}
          />
          {!editingItem && (
            <Input
              label="Contraseña"
              type="password"
              error={errors.password?.message}
              {...register("password", { required: "La contraseña es obligatoria." })}
            />
          )}
          <Controller
            control={control}
            name="activo"
            render={({ field }) => (
              <Switch label="Activo" checked={field.value} onChange={(event) => field.onChange(event.target.checked)} />
            )}
          />

          <div>
            <label style={{ display: "block", marginBottom: "var(--space-1)", fontSize: "var(--text-body)", color: "var(--text-secondary)" }}>
              Roles
            </label>
            <div style={{ display: "flex", gap: "var(--space-4)", flexWrap: "wrap" }}>
              {(roles ?? []).map((rol) => (
                <Controller
                  key={rol.id}
                  control={control}
                  name="rolesSeleccionados"
                  render={({ field }) => (
                    <Checkbox
                      label={rol.nombre}
                      checked={field.value.includes(rol.id)}
                      onChange={(event) => {
                        if (event.target.checked) {
                          field.onChange([...field.value, rol.id]);
                        } else {
                          field.onChange(field.value.filter((id) => id !== rol.id));
                        }
                      }}
                    />
                  )}
                />
              ))}
            </div>
            {perderiaAccesoAdmin && (
              <p style={{ color: "var(--danger)", fontSize: "var(--text-caption)", marginTop: "var(--space-2)" }}>
                Estás editando tu propio usuario: si guardas sin ningún rol que otorgue 'usuarios.administrar', perderás
                el acceso a esta sección.
              </p>
            )}
          </div>

        </form>
      </Modal>

      <CambiarPasswordModal usuario={passwordTarget} onClose={() => setPasswordTarget(null)} />
    </PageHeader>
  );
}

interface PasswordFormValues {
  password: string;
}

function CambiarPasswordModal({ usuario, onClose }: { usuario: UsuarioAdmin | null; onClose: () => void }) {
  const toast = useToast();
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PasswordFormValues>({ defaultValues: { password: "" } });

  const mutation = useMutation({
    mutationFn: (values: PasswordFormValues) => updateUsuario(usuario!.id, { password: values.password }),
    onSuccess: () => {
      toast.success(`Contraseña de '${usuario?.nombre}' actualizada correctamente.`);
      reset();
      onClose();
    },
    onError: (err) => setError(getApiErrorMessage(err, "No se pudo cambiar la contraseña.")),
  });

  const handleClose = () => {
    setError(null);
    reset();
    onClose();
  };

  return (
    <Modal
      open={Boolean(usuario)}
      onClose={handleClose}
      title={`Cambiar contraseña de ${usuario?.nombre ?? ""}`}
      footer={
        <>
          <Button type="button" variant="ghost" onClick={handleClose}>
            Cancelar
          </Button>
          <Button type="submit" form="password-form" variant="primary" loading={mutation.isPending}>
            Guardar
          </Button>
        </>
      }
    >
      <form id="password-form" onSubmit={handleSubmit((values) => mutation.mutate(values))} className={styles.form} noValidate>
        {error && <div className={styles.formError}>{error}</div>}
        <Input
          label="Nueva contraseña"
          type="password"
          error={errors.password?.message}
          {...register("password", { required: "La contraseña es obligatoria." })}
        />
      </form>
    </Modal>
  );
}
