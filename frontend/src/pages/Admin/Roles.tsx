import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listTodosLosRoles, listTodosLosUsuarios } from "../../api/admin";
import { Button, EmptyState, PageHeader, Table, type TableColumn } from "../../components/ui";
import { ordenarEnCliente, useOrdenamiento } from "../../hooks/useOrdenamiento";
import { usePageTitle } from "../../store/pageTitleStore";
import type { RolAdmin } from "../../api/admin";

interface RolConConteo extends RolAdmin {
  cantidadUsuarios: number;
}

export function Roles() {
  usePageTitle("Roles");
  const { ordenamiento, alternar: alternarOrden } = useOrdenamiento();

  // Roles se cargan completos (no hay paginación en el servidor): el orden
  // se hace en cliente.
  const { data: roles, isLoading, isError, refetch } = useQuery({
    queryKey: ["roles-admin"],
    queryFn: listTodosLosRoles,
  });

  const { data: usuarios } = useQuery({
    queryKey: ["usuarios-lookup-conteo"],
    queryFn: listTodosLosUsuarios,
  });

  const items = ordenarEnCliente<RolConConteo>(
    (roles ?? []).map((rol) => ({
      ...rol,
      cantidadUsuarios: (usuarios ?? []).filter((u) => u.roles.includes(rol.nombre)).length,
    })),
    ordenamiento,
    {
      nombre: (r) => r.nombre,
      permisos: (r) => r.permisos.length,
      usuarios: (r) => r.cantidadUsuarios,
    },
  );

  const columns: TableColumn<RolConConteo>[] = [
    {
      key: "nombre",
      header: "Rol",
      sortField: "nombre",
      render: (r) => (
        <Link to={`/admin/roles/${r.id}`} style={{ color: "var(--accent)", fontWeight: 500 }}>
          {r.nombre}
        </Link>
      ),
    },
    { key: "permisos", header: "Permisos asignados", sortField: "permisos", render: (r) => r.permisos.length },
    { key: "usuarios", header: "Usuarios con este rol", sortField: "usuarios", render: (r) => r.cantidadUsuarios },
  ];

  return (
    <PageHeader title="Roles" subtitle="Haz clic en un rol para editar sus permisos." breadcrumb={["Análisis", "Administración", "Roles"]}>
      {isError ? (
        <EmptyState
          title="No se pudo cargar"
          description="Hubo un problema al traer los roles."
          action={
            <Button variant="primary" onClick={() => refetch()}>
              Reintentar
            </Button>
          }
        />
      ) : !isLoading && items.length === 0 ? (
        <EmptyState title="Sin roles" description="Todavía no hay roles creados." />
      ) : (
        <Table
          columns={columns}
          data={items}
          getRowId={(row) => row.id}
          isLoading={isLoading}
          ordenamiento={ordenamiento}
          onOrdenar={alternarOrden}
        />
      )}
    </PageHeader>
  );
}
