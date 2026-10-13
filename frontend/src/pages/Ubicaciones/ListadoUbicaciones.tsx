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
import { Button, EmptyState, FormGrid, IconButton, Input, Modal, PageHeader, useToast } from "../../components/ui";
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

  const [deptoFormOpen, setDeptoFormOpen] = useState(false);
  const [editingDepto, setEditingDepto] = useState<Departamento | null>(null);
  const [deptoFormError, setDeptoFormError] = useState<string | null>(null);

  const [municipioFormOpen, setMunicipioFormOpen] = useState(false);
  const [editingMunicipio, setEditingMunicipio] = useState<Municipio | null>(null);
  const [municipioFormError, setMunicipioFormError] = useState<string | null>(null);

  const { data: departamentos, isLoading: cargandoDeptos } = useQuery({
    queryKey: ["departamentos", searchDepto],
    queryFn: () => listDepartamentos(1, searchDepto),
  });

  const { data: municipios, isLoading: cargandoMunicipios } = useQuery({
    queryKey: ["municipios-de-departamento", selectedDepto?.id, searchMunicipio],
    queryFn: () => listMunicipiosDeDepartamento(selectedDepto!.id, 1, searchMunicipio),
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
            onChange={(e) => setSearchDepto(e.target.value)}
            aria-label="Buscar departamento"
          />
        </div>
        <div className={styles.list}>
          {!cargandoDeptos && (departamentos?.items.length ?? 0) === 0 && (
            <div style={{ padding: "var(--space-4)" }}>
              <EmptyState title="Sin departamentos" description="No hay departamentos que coincidan." />
            </div>
          )}
          {(departamentos?.items ?? []).map((d) => (
            <button
              key={d.id}
              type="button"
              className={[styles.listItem, selectedDepto?.id === d.id ? styles.listItemActive : ""].join(" ")}
              onClick={() => {
                setSelectedDepto(d);
                setSearchMunicipio("");
              }}
            >
              <span>{d.nombre}</span>
              <span className={styles.listItemActions}>
                <IconButton
                  label={puedeEscribir ? `Editar ${d.nombre}` : READ_ONLY_TITLE}
                  icon={<Pencil size={14} />}
                  onClick={(event) => {
                    event.stopPropagation();
                    openEditDepto(d);
                  }}
                  disabled={!puedeEscribir}
                />
              </span>
            </button>
          ))}
        </div>
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
                onChange={(e) => setSearchMunicipio(e.target.value)}
                aria-label="Buscar municipio"
              />
            </div>
            <div className={styles.list}>
              {!cargandoMunicipios && (municipios?.items.length ?? 0) === 0 && (
                <div style={{ padding: "var(--space-4)" }}>
                  <EmptyState title="Sin municipios" description="Este departamento no tiene municipios registrados." />
                </div>
              )}
              {(municipios?.items ?? []).map((m) => (
                <div key={m.id} className={styles.listItem} style={{ cursor: "default" }}>
                  <span>
                    {m.nombre} <span className="font-mono-data" style={{ color: "var(--text-secondary)" }}>({m.codigo_dane})</span>
                  </span>
                  <span className={styles.listItemActions}>
                    <IconButton
                      label={puedeEscribir ? `Editar ${m.nombre}` : READ_ONLY_TITLE}
                      icon={<Pencil size={14} />}
                      onClick={() => openEditMunicipio(m)}
                      disabled={!puedeEscribir}
                    />
                  </span>
                </div>
              ))}
            </div>
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

