import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MapPin, Pencil, Plus } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { getApiErrorMessage } from "../../api/errors";
import {
  createDepartamento,
  createMunicipio,
  listDepartamentos,
  listMunicipiosDeDepartamento,
  updateDepartamento,
  updateMunicipio,
  type Departamento,
  type Municipio,
} from "../../api/ubicaciones";
import {
  Button,
  EmptyState,
  FormGrid,
  IconButton,
  Input,
  Modal,
  PageHeader,
  SelectorFilasPorPagina,
  Table,
  guardarFilasPorPagina,
  leerFilasPorPaginaGuardadas,
  rangoRegistros,
  useToast,
  type TableColumn,
} from "../../components/ui";
import tableStyles from "../../components/ui/Table.module.css";
import { useOrdenamiento } from "../../hooks/useOrdenamiento";
import { canWrite } from "../../lib/permissions";
import { useAuthStore } from "../../store/authStore";
import { usePageTitle } from "../../store/pageTitleStore";
import crudStyles from "../../components/CatalogoCRUD.module.css";
import styles from "./Ubicaciones.module.css";

const READ_ONLY_TITLE = "No tienes permiso para esta acción (rol Solo Consulta)";

interface DepartamentoFormValues {
  codigo_dane: string;
  nombre: string;
}

interface MunicipioFormValues {
  codigo_dane: string;
  nombre: string;
}

export function ListadoUbicaciones() {
  usePageTitle("Ubicaciones");
  const user = useAuthStore((state) => state.user);
  const puedeEscribir = canWrite(user);
  const toast = useToast();
  const queryClient = useQueryClient();

  const [searchDepto, setSearchDepto] = useState("");
  const [selectedDepto, setSelectedDepto] = useState<Departamento | null>(null);
  const [searchMunicipio, setSearchMunicipio] = useState("");

  const [deptoPage, setDeptoPage] = useState(1);
  const [deptoPageSize, setDeptoPageSize] = useState(() => leerFilasPorPaginaGuardadas("ubicaciones:departamentos", 50));
  const [municipioPage, setMunicipioPage] = useState(1);
  const [municipioPageSize, setMunicipioPageSize] = useState(() => leerFilasPorPaginaGuardadas("ubicaciones:municipios", 50));

  const [deptoFormOpen, setDeptoFormOpen] = useState(false);
  const [editingDepto, setEditingDepto] = useState<Departamento | null>(null);
  const [deptoFormError, setDeptoFormError] = useState<string | null>(null);

  const [municipioFormOpen, setMunicipioFormOpen] = useState(false);
  const [editingMunicipio, setEditingMunicipio] = useState<Municipio | null>(null);
  const [municipioFormError, setMunicipioFormError] = useState<string | null>(null);

  // Orden en el servidor (las dos listas están paginadas).
  const { ordenamiento: ordenDeptos, alternar: alternarOrdenDeptos } = useOrdenamiento();
  const { ordenamiento: ordenMunicipios, alternar: alternarOrdenMunicipios } = useOrdenamiento();

  const { data: departamentos, isLoading: cargandoDeptos, isError: errorDeptos, refetch: refetchDeptos } = useQuery({
    queryKey: ["departamentos", deptoPage, deptoPageSize, searchDepto, ordenDeptos],
    queryFn: () => listDepartamentos(deptoPage, searchDepto, deptoPageSize, ordenDeptos),
  });

  const {
    data: municipios,
    isLoading: cargandoMunicipios,
    isError: errorMunicipios,
    refetch: refetchMunicipios,
  } = useQuery({
    queryKey: ["municipios-de-departamento", selectedDepto?.id, municipioPage, municipioPageSize, searchMunicipio, ordenMunicipios],
    queryFn: () =>
      listMunicipiosDeDepartamento(selectedDepto!.id, municipioPage, searchMunicipio, municipioPageSize, ordenMunicipios),
    enabled: selectedDepto != null,
  });

  // --- departamento form ---
  const deptoForm = useForm<DepartamentoFormValues>({ defaultValues: { codigo_dane: "", nombre: "" } });

  const openCreateDepto = () => {
    setEditingDepto(null);
    setDeptoFormError(null);
    deptoForm.reset({ codigo_dane: "", nombre: "" });
    setDeptoFormOpen(true);
  };

  const openEditDepto = (d: Departamento) => {
    setEditingDepto(d);
    setDeptoFormError(null);
    deptoForm.reset({ codigo_dane: d.codigo_dane, nombre: d.nombre });
    setDeptoFormOpen(true);
  };

  const deptoMutation = useMutation({
    mutationFn: (values: DepartamentoFormValues) =>
      editingDepto ? updateDepartamento(editingDepto.id, { ...values }) : createDepartamento({ ...values }),
    onSuccess: (depto) => {
      queryClient.invalidateQueries({ queryKey: ["departamentos"] });
      setDeptoFormOpen(false);
      toast.success(`Departamento '${depto.nombre}' guardado correctamente.`);
      if (selectedDepto?.id === depto.id) setSelectedDepto(depto);
    },
    onError: (error) => setDeptoFormError(getApiErrorMessage(error, "No se pudo guardar el departamento.")),
  });

  // --- municipio form ---
  const municipioForm = useForm<MunicipioFormValues>({ defaultValues: { codigo_dane: "", nombre: "" } });

  const openCreateMunicipio = () => {
    setEditingMunicipio(null);
    setMunicipioFormError(null);
    municipioForm.reset({ codigo_dane: "", nombre: "" });
    setMunicipioFormOpen(true);
  };

  const openEditMunicipio = (m: Municipio) => {
    setEditingMunicipio(m);
    setMunicipioFormError(null);
    municipioForm.reset({ codigo_dane: m.codigo_dane, nombre: m.nombre });
    setMunicipioFormOpen(true);
  };

  const municipioMutation = useMutation({
    mutationFn: (values: MunicipioFormValues) =>
      editingMunicipio
        ? updateMunicipio(editingMunicipio.id, { ...values })
        : createMunicipio({ ...values, departamento_id: selectedDepto!.id }),
    onSuccess: (municipio) => {
      queryClient.invalidateQueries({ queryKey: ["municipios-de-departamento"] });
      setMunicipioFormOpen(false);
      toast.success(`Municipio '${municipio.nombre}' guardado correctamente.`);
    },
    onError: (error) => setMunicipioFormError(getApiErrorMessage(error, "No se pudo guardar el municipio.")),
  });

  const columnaDane = <T extends { codigo_dane: string }>(): TableColumn<T> => ({
    key: "codigo_dane",
    header: "Código DANE",
    sortField: "codigo_dane",
    monoData: true,
    render: (fila) => fila.codigo_dane,
  });

  const columnasDeptos: TableColumn<Departamento>[] = [
    {
      key: "nombre",
      header: "Departamento",
      sortField: "nombre",
      render: (d) => (
        <button
          type="button"
          className={styles.selectorFila}
          aria-pressed={selectedDepto?.id === d.id}
          onClick={() => {
            setSelectedDepto(d);
            setSearchMunicipio("");
            setMunicipioPage(1);
          }}
        >
          {d.nombre}
        </button>
      ),
    },
    columnaDane<Departamento>(),
    {
      key: "acciones",
      header: "Acciones",
      align: "right",
      render: (d) => (
        <IconButton
          label={puedeEscribir ? `Editar ${d.nombre}` : READ_ONLY_TITLE}
          icon={<Pencil size={14} />}
          onClick={() => openEditDepto(d)}
          disabled={!puedeEscribir}
        />
      ),
    },
  ];

  const columnasMunicipios: TableColumn<Municipio>[] = [
    { key: "nombre", header: "Municipio", sortField: "nombre", render: (m) => m.nombre },
    columnaDane<Municipio>(),
    {
      key: "acciones",
      header: "Acciones",
      align: "right",
      render: (m) => (
        <IconButton
          label={puedeEscribir ? `Editar ${m.nombre}` : READ_ONLY_TITLE}
          icon={<Pencil size={14} />}
          onClick={() => openEditMunicipio(m)}
          disabled={!puedeEscribir}
        />
      ),
    },
  ];

  return (
    <PageHeader title="Ubicaciones" breadcrumb={["Datos", "Ubicaciones"]}>
    <div className={styles.grid}>
      <div className={styles.panel}>
        <div className={styles.panelHeader}>
          <span className={styles.panelTitle}>Departamentos</span>
          <Button
            variant="primary"
            leftIcon={<Plus size={14} />}
            onClick={openCreateDepto}
            disabled={!puedeEscribir}
            title={puedeEscribir ? undefined : READ_ONLY_TITLE}
          >
            Nuevo
          </Button>
        </div>
        <div style={{ padding: "var(--space-3) var(--space-4)" }}>
          <Input
            placeholder="Buscar departamento…"
            value={searchDepto}
            onChange={(e) => {
              setSearchDepto(e.target.value);
              setDeptoPage(1);
            }}
            aria-label="Buscar departamento"
          />
        </div>
        <div className={styles.list}>
          {errorDeptos && (
            <div style={{ padding: "var(--space-4)" }}>
              <EmptyState
                title="No se pudo cargar"
                description="Hubo un problema al traer los departamentos."
                action={
                  <Button variant="primary" onClick={() => refetchDeptos()}>
                    Reintentar
                  </Button>
                }
              />
            </div>
          )}
          {!errorDeptos && !cargandoDeptos && (departamentos?.items.length ?? 0) === 0 && (
            <div style={{ padding: "var(--space-4)" }}>
              <EmptyState title="Sin departamentos" description="No hay departamentos que coincidan." />
            </div>
          )}
          {!errorDeptos && (cargandoDeptos || (departamentos?.items.length ?? 0) > 0) && (
            <Table
              columns={columnasDeptos}
              data={departamentos?.items ?? []}
              getRowId={(d) => d.id}
              isLoading={cargandoDeptos}
              compacta
              getRowClassName={(d) => (selectedDepto?.id === d.id ? tableStyles.rowSelected : undefined)}
              ordenamiento={ordenDeptos}
              onOrdenar={(campo) => {
                alternarOrdenDeptos(campo);
                setDeptoPage(1);
              }}
            />
          )}
        </div>
        {departamentos && (
          <div className={crudStyles.pagination}>
            <span>{rangoRegistros(departamentos.page, departamentos.page_size, departamentos.total)}</span>
            <SelectorFilasPorPagina
              value={deptoPageSize}
              onChange={(n) => {
                setDeptoPageSize(n);
                guardarFilasPorPagina("ubicaciones:departamentos", n);
                setDeptoPage(1);
              }}
            />
            <Button
              variant="ghost"
              onClick={() => setDeptoPage((p) => Math.max(1, p - 1))}
              disabled={deptoPage <= 1}
            >
              Anterior
            </Button>
            <Button
              variant="ghost"
              onClick={() =>
                setDeptoPage((p) =>
                  Math.min(Math.max(1, Math.ceil(departamentos.total / departamentos.page_size)), p + 1),
                )
              }
              disabled={deptoPage >= Math.max(1, Math.ceil(departamentos.total / departamentos.page_size))}
            >
              Siguiente
            </Button>
          </div>
        )}
      </div>

      <div className={styles.panel}>
        <div className={styles.panelHeader}>
          <span className={styles.panelTitle}>
            {selectedDepto ? `Municipios de ${selectedDepto.nombre}` : "Municipios"}
          </span>
          {selectedDepto && (
            <Button
              variant="primary"
              leftIcon={<Plus size={14} />}
              onClick={openCreateMunicipio}
              disabled={!puedeEscribir}
              title={puedeEscribir ? undefined : READ_ONLY_TITLE}
            >
              Nuevo
            </Button>
          )}
        </div>

        {!selectedDepto ? (
          <div style={{ padding: "var(--space-6)" }}>
            <EmptyState
              icon={<MapPin size={32} strokeWidth={1.5} />}
              title="Selecciona un departamento"
              description="Elige un departamento de la lista para ver sus municipios."
            />
          </div>
        ) : (
          <>
            <div style={{ padding: "var(--space-3) var(--space-4)" }}>
              <Input
                placeholder="Buscar municipio…"
                value={searchMunicipio}
                onChange={(e) => {
                  setSearchMunicipio(e.target.value);
                  setMunicipioPage(1);
                }}
                aria-label="Buscar municipio"
              />
            </div>
            <div className={styles.list}>
              {errorMunicipios && (
                <div style={{ padding: "var(--space-4)" }}>
                  <EmptyState
                    title="No se pudo cargar"
                    description="Hubo un problema al traer los municipios."
                    action={
                      <Button variant="primary" onClick={() => refetchMunicipios()}>
                        Reintentar
                      </Button>
                    }
                  />
                </div>
              )}
              {!errorMunicipios && !cargandoMunicipios && (municipios?.items.length ?? 0) === 0 && (
                <div style={{ padding: "var(--space-4)" }}>
                  <EmptyState title="Sin municipios" description="Este departamento no tiene municipios registrados." />
                </div>
              )}
              {!errorMunicipios && (cargandoMunicipios || (municipios?.items.length ?? 0) > 0) && (
                <Table
                  columns={columnasMunicipios}
                  data={municipios?.items ?? []}
                  getRowId={(m) => m.id}
                  isLoading={cargandoMunicipios}
                  compacta
                  ordenamiento={ordenMunicipios}
                  onOrdenar={(campo) => {
                    alternarOrdenMunicipios(campo);
                    setMunicipioPage(1);
                  }}
                />
              )}
            </div>
            {municipios && (
              <div className={crudStyles.pagination}>
                <span>{rangoRegistros(municipios.page, municipios.page_size, municipios.total)}</span>
                <SelectorFilasPorPagina
                  value={municipioPageSize}
                  onChange={(n) => {
                    setMunicipioPageSize(n);
                    guardarFilasPorPagina("ubicaciones:municipios", n);
                    setMunicipioPage(1);
                  }}
                />
                <Button
                  variant="ghost"
                  onClick={() => setMunicipioPage((p) => Math.max(1, p - 1))}
                  disabled={municipioPage <= 1}
                >
                  Anterior
                </Button>
                <Button
                  variant="ghost"
                  onClick={() =>
                    setMunicipioPage((p) =>
                      Math.min(Math.max(1, Math.ceil(municipios.total / municipios.page_size)), p + 1),
                    )
                  }
                  disabled={municipioPage >= Math.max(1, Math.ceil(municipios.total / municipios.page_size))}
                >
                  Siguiente
                </Button>
              </div>
            )}
          </>
        )}
      </div>

      <Modal
        open={deptoFormOpen}
        onClose={() => setDeptoFormOpen(false)}
        title={editingDepto ? "Editar departamento" : "Nuevo departamento"}
        footer={
          <>
            <Button type="button" variant="ghost" onClick={() => setDeptoFormOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" form="depto-form" variant="primary" loading={deptoMutation.isPending}>
              Guardar
            </Button>
          </>
        }
      >
        <form id="depto-form" onSubmit={deptoForm.handleSubmit((values) => deptoMutation.mutate(values))} className={crudStyles.form} noValidate>
          {deptoFormError && <div className={crudStyles.formError}>{deptoFormError}</div>}
          <FormGrid columns={2}>
            <Input
              label="Código DANE"
              required
              monoData
              error={deptoForm.formState.errors.codigo_dane?.message}
              {...deptoForm.register("codigo_dane", { required: "El código DANE es obligatorio." })}
            />
            <Input
              label="Nombre"
              required
              error={deptoForm.formState.errors.nombre?.message}
              {...deptoForm.register("nombre", { required: "El nombre es obligatorio." })}
            />
          </FormGrid>
        </form>
      </Modal>

      <Modal
        open={municipioFormOpen}
        onClose={() => setMunicipioFormOpen(false)}
        title={editingMunicipio ? "Editar municipio" : `Nuevo municipio en ${selectedDepto?.nombre ?? ""}`}
        footer={
          <>
            <Button type="button" variant="ghost" onClick={() => setMunicipioFormOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" form="municipio-form" variant="primary" loading={municipioMutation.isPending}>
              Guardar
            </Button>
          </>
        }
      >
        <form
          id="municipio-form"
          onSubmit={municipioForm.handleSubmit((values) => municipioMutation.mutate(values))}
          className={crudStyles.form}
          noValidate
        >
          {municipioFormError && <div className={crudStyles.formError}>{municipioFormError}</div>}
          <FormGrid columns={2}>
            <Input
              label="Código DANE"
              required
              monoData
              error={municipioForm.formState.errors.codigo_dane?.message}
              {...municipioForm.register("codigo_dane", { required: "El código DANE es obligatorio." })}
            />
            <Input
              label="Nombre"
              required
              error={municipioForm.formState.errors.nombre?.message}
              {...municipioForm.register("nombre", { required: "El nombre es obligatorio." })}
            />
          </FormGrid>
        </form>
      </Modal>
    </div>
    </PageHeader>
  );
}

