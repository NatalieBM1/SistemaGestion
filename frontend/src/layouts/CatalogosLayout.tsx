import { NavLink, Outlet } from "react-router-dom";
import { PageHeader } from "../components/ui";
import { CATALOGOS, CATALOGO_ORDER } from "../config/catalogos";
import tabsStyles from "../components/ui/TabsBar.module.css";

export function CatalogosLayout() {
  return (
    <PageHeader title="Catálogos" breadcrumb={["Datos", "Catálogos"]}>
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
