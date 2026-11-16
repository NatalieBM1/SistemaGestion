import { NavLink, Outlet, useLocation } from "react-router-dom";
import { PageHeader } from "../components/ui";
import { CATALOGOS, CATALOGO_ORDER } from "../config/catalogos";
import tabsStyles from "../components/ui/TabsBar.module.css";
import { AYUDA, AYUDA_CATALOGOS } from "../ayuda/rutas";

export function CatalogosLayout() {
  const location = useLocation();
  const catalogoActual = location.pathname.split("/")[2] ?? "";
  return (
    <PageHeader
      ayuda={AYUDA_CATALOGOS[catalogoActual] ?? AYUDA.catalogos} title="Catálogos" breadcrumb={["Datos", "Catálogos"]}>
      <div className={tabsStyles.tabs} role="tablist">
        {CATALOGO_ORDER.map((slug) => (
          <NavLink
            key={slug}
            to={`/catalogos/${slug}`}
            role="tab"
            className={({ isActive }) =>
              [tabsStyles.tab, isActive ? tabsStyles.tabActive : ""].filter(Boolean).join(" ")
            }
          >
            {CATALOGOS[slug].title}
          </NavLink>
        ))}
      </div>
      <Outlet />
    </PageHeader>
  );
}
