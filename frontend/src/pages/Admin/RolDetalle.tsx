import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getApiErrorMessage } from "../../api/errors";
import {
  asignarPermisoARol,
  getRol,
  listTodosLosPermisos,
  listTodosLosRoles,
  quitarPermisoDeRol,
} from "../../api/admin";
import { Button, Checkbox, PageHeader, useToast } from "../../components/ui";
import { useAuthStore } from "../../store/authStore";
import { usePageTitle } from "../../store/pageTitleStore";
import styles from "../../components/CatalogoCRUD.module.css";

const PERMISO_ADMIN = "usuarios.administrar";

const NOMBRE_MODULO: Record<string, string> = {
  catalogos: "Catálogos",
  remisiones: "Remisiones",
  facturas: "Facturación",
  terceros: "Terceros",
  ubicaciones: "Ubicaciones",
  activos: "Activos",
  usuarios: "Usuarios",
};

function nombreDeModulo(modulo: string): string {
  return NOMBRE_MODULO[modulo] ?? modulo.charAt(0).toUpperCase() + modulo.slice(1);
}

export function RolDetalle() {
  const params = useParams<{ id: string }>();
  const rolId = Number(params.id);
  const navigate = useNavigate();
  const toast = useToast();
  const queryClient = useQueryClient();
  const currentUser = useAuthStore((state) => state.user);

  const [seleccionados, setSeleccionados] = useState<Set<number>>(new Set());
  const [error, setError] = useState<string | null>(null);

  const { data: rol } = useQuery({
    queryKey: ["rol-admin", rolId],
    queryFn: () => getRol(rolId),
  });

  usePageTitle(rol ? `Rol: ${rol.nombre}` : "Rol");

  const { data: permisos } = useQuery({
    queryKey: ["permisos-lookup"],
    queryFn: listTodosLosPermisos,
  });

  const { data: todosLosRoles } = useQuery({
    queryKey: ["roles-admin"],
    queryFn: listTodosLosRoles,
  });

  useEffect(() => {
    if (!rol || !permisos) return;
    const ids = permisos.filter((p) => rol.permisos.includes(p.codigo)).map((p) => p.id);
    setSeleccionados(new Set(ids));
  }, [rol, permisos]);

  const idPermisoAdmin = permisos?.find((p) => p.codigo === PERMISO_ADMIN)?.id;

  const esRolPropio = rol != null && currentUser != null && currentUser.roles.includes(rol.nombre);
  const otrosRolesTienenAdmin = (todosLosRoles ?? [])
    .filter((r) => r.id !== rolId && currentUser?.roles.includes(r.nombre))
    .some((r) => r.permisos.includes(PERMISO_ADMIN));
  const perderiaAccesoAdmin =
    esRolPropio &&
    idPermisoAdmin != null &&
    !seleccionados.has(idPermisoAdmin) &&
    !otrosRolesTienenAdmin;

  const toggle = (permisoId: number, checked: boolean) => {
    setSeleccionados((current) => {
      const next = new Set(current);
      if (checked) next.add(permisoId);
      else next.delete(permisoId);
      return next;
    });
  };

  const mutation = useMutation({
    mutationFn: async () => {
      const idsOriginales = new Set((permisos ?? []).filter((p) => rol?.permisos.includes(p.codigo)).map((p) => p.id));
      const aAsignar = [...seleccionados].filter((id) => !idsOriginales.has(id));
      const aQuitar = [...idsOriginales].filter((id) => !seleccionados.has(id));
      await Promise.all([
        ...aAsignar.map((permisoId) => asignarPermisoARol(rolId, permisoId)),
        ...aQuitar.map((permisoId) => quitarPermisoDeRol(rolId, permisoId)),
      ]);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rol-admin", rolId] });
      queryClient.invalidateQueries({ queryKey: ["roles-admin"] });
      toast.success(`Permisos del rol '${rol?.nombre}' actualizados correctamente.`);
    },
    onError: (err) => setError(getApiErrorMessage(err, "No se pudieron guardar los permisos.")),
  });

  const handleGuardar = () => {
    setError(null);
    if (perderiaAccesoAdmin) {
      setError(
        `No puedes quitar el permiso '${PERMISO_ADMIN}' del rol '${rol?.nombre}': es el único rol tuyo que te da acceso a esta sección y te quedarías afuera.`,
      );
      return;
    }
    mutation.mutate();
  };

  const permisosPorModulo = new Map<string, typeof permisos>();
  for (const permiso of permisos ?? []) {
    const lista = permisosPorModulo.get(permiso.modulo) ?? [];
    lista.push(permiso);
    permisosPorModulo.set(permiso.modulo, lista);
  }

  return (
    <PageHeader
      title={rol?.nombre ?? "Rol"}
      subtitle="Marca los permisos que debe tener este rol, agrupados por módulo."
      breadcrumb={["Análisis", { label: "Administración", to: "/admin/usuarios" }, { label: "Roles", to: "/admin/roles" }]}
      actions={
        <>
          <Button variant="ghost" onClick={() => navigate("/admin/roles")}>
            Cancelar
          </Button>
          <Button variant="primary" loading={mutation.isPending} onClick={handleGuardar}>
            Guardar permisos
          </Button>
        </>
      }
    >
      {error && <div className={styles.formError} style={{ marginBottom: "var(--space-4)" }}>{error}</div>}
      {perderiaAccesoAdmin && !error && (
        <div className={styles.formError} style={{ marginBottom: "var(--space-4)" }}>
          Estás editando un rol que tienes asignado: si quitas '{PERMISO_ADMIN}' aquí y no tienes ese permiso por
          ningún otro rol, perderás el acceso a esta sección.
        </div>
      )}

      <div style={{ display: "grid", gap: "var(--space-5)" }}>
        {[...permisosPorModulo.entries()].map(([modulo, lista]) => (
          <div key={modulo}>
            <h3 style={{ margin: "0 0 var(--space-2)" }}>{nombreDeModulo(modulo)}</h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "var(--space-2)" }}>
              {(lista ?? []).map((permiso) => (
                <Checkbox
                  key={permiso.id}
                  label={permiso.codigo}
                  checked={seleccionados.has(permiso.id)}
                  onChange={(event) => toggle(permiso.id, event.target.checked)}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </PageHeader>
  );
}
