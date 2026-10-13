import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import {
  type CatalogoItem,
  createCatalogoItem,
  deleteCatalogoItem,
  listCatalogo,
  updateCatalogoItem,
} from "../api/catalogos";
import { getApiErrorMessage } from "../api/errors";
import {
  Button,
  Checkbox,
  EmptyState,
  FilterPanel,
  FormGrid,
  IconButton,
  Input,
  Modal,
  Table,
  type TableColumn,
  useToast,
} from "./ui";
import type { CatalogoConfig } from "../config/catalogos";
import { canWrite } from "../lib/permissions";
import { useAuthStore } from "../store/authStore";
import { usePageTitle } from "../store/pageTitleStore";
import styles from "./CatalogoCRUD.module.css";

interface CatalogoCRUDProps {
  config: CatalogoConfig;
}

const READ_ONLY_TITLE = "No tienes permiso para esta acción (rol Solo Consulta)";

export function CatalogoCRUD({ config }: CatalogoCRUDProps) {
  usePageTitle(config.title);

  const user = useAuthStore((state) => state.user);
  const puedeEscribir = canWrite(user);
  const toast = useToast();
  const queryClient = useQueryClient();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<CatalogoItem | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<CatalogoItem | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    setPage(1);
    setSearch("");
  }, [config.slug]);

  const queryKey = ["catalogo", config.slug, page, search];
  const { data, isLoading } = useQuery({
    queryKey,
    queryFn: () => listCatalogo(config.endpoint, page, search),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["catalogo", config.slug] });

  const createMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => createCatalogoItem(config.endpoint, payload),
    onSuccess: () => {
      invalidate();
      setFormOpen(false);
      toast.success(`${config.singular} creado correctamente.`);
    },
    onError: (error) => setFormError(getApiErrorMessage(error, "No se pudo crear el registro.")),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Record<string, unknown> }) =>
      updateCatalogoItem(config.endpoint, id, payload),
    onSuccess: () => {
      invalidate();
      setFormOpen(false);
      toast.success(`${config.singular} actualizado correctamente.`);
    },
    onError: (error) => setFormError(getApiErrorMessage(error, "No se pudo actualizar el registro.")),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteCatalogoItem(config.endpoint, id),
    onSuccess: () => {
      invalidate();
      setDeleteTarget(null);
      toast.success(`${config.singular} eliminado correctamente.`);
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "No se pudo eliminar el registro."));
      setDeleteTarget(null);
    },
  });

  const openCreateForm = () => {
    setEditingItem(null);
    setFormError(null);
    setFormOpen(true);
  };

  const openEditForm = (item: CatalogoItem) => {
    setEditingItem(item);
    setFormError(null);
    setFormOpen(true);
  };

  const handleSubmitForm = (payload: Record<string, unknown>) => {
    if (editingItem) {
      updateMutation.mutate({ id: editingItem.id, payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const columns: TableColumn<CatalogoItem>[] = [
    ...config.columns.map<TableColumn<CatalogoItem>>((column) => ({
      key: column.key,
      header: column.header,
      monoData: column.monoData,
      render: (row) => formatCellValue(row[column.key]),
    })),
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
            label={puedeEscribir ? "Eliminar" : READ_ONLY_TITLE}
            icon={<Trash2 size={16} />}
            onClick={() => setDeleteTarget(row)}
            disabled={!puedeEscribir}
          />
        </div>
      ),
    },
  ];

  const items = data?.items ?? [];
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <div>
      <FilterPanel
        search={
          <Input
            placeholder={config.searchPlaceholder}
            leftElement={<Search size={16} aria-hidden="true" />}
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
            aria-label="Buscar"
          />
        }
        footer={
          <Button
            variant="primary"
            leftIcon={<Plus size={16} />}
            onClick={openCreateForm}
            disabled={!puedeEscribir}
            title={puedeEscribir ? undefined : READ_ONLY_TITLE}
            style={{ marginLeft: "auto" }}
          >
            Nuevo {config.singular}
          </Button>
        }
      />

      {!isLoading && items.length === 0 ? (
        <EmptyState
          icon={<Search size={32} strokeWidth={1.5} />}
          title={`Sin resultados en ${config.title.toLowerCase()}`}
          description={
            search
              ? "No encontramos registros que coincidan con tu búsqueda."
              : `Todavía no hay ningún registro. Crea el primer ${config.singular.toLowerCase()}.`
          }
          action={
            !search && (
              <Button variant="primary" onClick={openCreateForm} disabled={!puedeEscribir}>
                Nuevo {config.singular}
              </Button>
            )
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
              <Button
                variant="ghost"
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                disabled={page <= 1}
              >
                Anterior
              </Button>
              <Button
                variant="ghost"
                onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
                disabled={page >= totalPages}
              >
                Siguiente
              </Button>
            </div>
          )}
        </>
      )}

      <Modal
        open={formOpen}
        onClose={() => setFormOpen(false)}
        title={editingItem ? `Editar ${config.singular}` : `Nuevo ${config.singular}`}
        footer={
          <>
            <Button type="button" variant="ghost" onClick={() => setFormOpen(false)}>
              Cancelar
            </Button>
            <Button
              type="submit"
              form="catalogo-form"
              variant="primary"
              loading={createMutation.isPending || updateMutation.isPending}
            >
              Guardar
            </Button>
          </>
        }
      >
        <CatalogoForm
          config={config}
          initialValues={editingItem}
          error={formError}
          onSubmit={handleSubmitForm}
        />
      </Modal>

      <Modal
        open={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        title="Confirmar eliminación"
        size="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setDeleteTarget(null)}>
              Cancelar
            </Button>
            <Button
              variant="danger"
              loading={deleteMutation.isPending}
              onClick={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
            >
              Eliminar
            </Button>
          </>
        }
      >
        <p className={styles.confirmText}>
          ¿Seguro que quieres eliminar este {config.singular.toLowerCase()}? Esta acción no se puede
          deshacer.
        </p>
      </Modal>
    </div>
  );
}

function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "boolean") return value ? "Sí" : "No";
  return String(value);
}

interface CatalogoFormProps {
  config: CatalogoConfig;
  initialValues: CatalogoItem | null;
  error: string | null;
  onSubmit: (payload: Record<string, unknown>) => void;
}

function CatalogoForm({ config, initialValues, error, onSubmit }: CatalogoFormProps) {
  const defaultValues: Record<string, unknown> = {};
  for (const field of config.fields) {
    if (initialValues) {
      defaultValues[field.name] = initialValues[field.name] ?? (field.type === "checkbox" ? false : "");
    } else {
      defaultValues[field.name] = field.type === "checkbox" ? false : field.type === "number" ? 0 : "";
    }
  }

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({ defaultValues });

  const submitHandler = handleSubmit((values) => {
    const payload: Record<string, unknown> = {};
    for (const field of config.fields) {
      const raw = values[field.name];
      if (field.type === "number") {
        payload[field.name] = raw === "" || raw === undefined ? undefined : Number(raw);
      } else if (field.type === "text" && raw === "") {
        payload[field.name] = undefined;
      } else {
        payload[field.name] = raw;
      }
    }
    onSubmit(payload);
  });

  return (
    <form id="catalogo-form" className={styles.form} onSubmit={submitHandler} noValidate>
      {error && <div className={styles.formError}>{error}</div>}

      <FormGrid columns={2}>
        {config.fields.map((field) => {
          if (field.type === "checkbox") {
            return <Checkbox key={field.name} label={field.label} {...register(field.name)} />;
          }
          return (
            <Input
              key={field.name}
              label={field.label}
              required={field.required}
              type={field.type === "number" ? "number" : "text"}
              monoData={field.monoData}
              error={errors[field.name]?.message as string | undefined}
              {...register(field.name, {
                required: field.required ? `${field.label} es obligatorio.` : false,
              })}
            />
          );
        })}
      </FormGrid>
    </form>
  );
}
