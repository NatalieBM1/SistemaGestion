import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listTodosLosRoles, listTodosLosUsuarios } from "../../api/admin";
import { PageHeader, Table, type TableColumn } from "../../components/ui";
import { usePageTitle } from "../../store/pageTitleStore";
import type { RolAdmin } from "../../api/admin";

interface RolConConteo extends RolAdmin {
  cantidadUsuarios: number;
}

export function Roles() {
  usePageTitle("Roles");

  const { data: roles, isLoading } = useQuery({
    queryKey: ["roles-admin"],
    queryFn: listTodosLosRoles,
  });

  const { data: usuarios } = useQuery({
    queryKey: ["usuarios-lookup-conteo"],
    queryFn: listTodosLosUsuarios,
  });

  const items: RolConConteo[] = (roles ?? []).map((rol) => ({
    ...rol,
    cantidadUsuarios: (usuarios ?? []).filter((u) => u.roles.includes(rol.nombre)).length,
  }));

  const columns: TableColumn<RolConConteo>[] = [
    {
      key: "nombre",
      header: "Rol",
      render: (r) => (
        <Link to={`/admin/roles/${r.id}`} style={{ color: "var(--accent)", fontWeight: 500 }}>
          {r.nombre}
        </Link>
      ),
    },
    { key: "permisos", header: "Permisos asignados", render: (r) => r.permisos.length },
    { key: "usuarios", header: "Usuarios con este rol", render: (r) => r.cantidadUsuarios },
  ];

  return (
    <PageHeader title="Roles" subtitle="Haz clic en un rol para editar sus permisos." breadcrumb={["Análisis", "Administración", "Roles"]}>
      <Table columns={columns} data={items} getRowId={(row) => row.id} isLoading={isLoading} />
    </PageHeader>
  );
}
