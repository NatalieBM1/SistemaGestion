import { BarChart3, Car, LayoutDashboard, LayoutGrid, LogOut, Map, Menu, Receipt, ShieldCheck, Truck, Users, X } from "lucide-react";
import { useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import logo from "../assets/Logo_Transportes.png";
import { hasPermission } from "../lib/permissions";
import { usePageTitleStore } from "../store/pageTitleStore";
import { useAuthStore } from "../store/authStore";
import styles from "./MainLayout.module.css";

interface NavItem {
  label: string;
  path: string;
  icon: typeof LayoutGrid;
  activePrefix?: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Inicio", path: "/", icon: LayoutDashboard },
  { label: "Catálogos", path: "/catalogos", icon: LayoutGrid },
  { label: "Remisiones", path: "/remisiones", icon: Truck },
  { label: "Facturación", path: "/facturas", icon: Receipt },
  { label: "Terceros", path: "/terceros", icon: Users },
  { label: "Ubicaciones", path: "/ubicaciones", icon: Map },
  { label: "Activos", path: "/activos", icon: Car },
  { label: "Reportes", path: "/reportes", icon: BarChart3 },
];

const NAV_ITEM_ADMIN: NavItem = {
  label: "Administración",
  path: "/admin/usuarios",
  icon: ShieldCheck,
  activePrefix: "/admin",
};

export function MainLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const title = usePageTitleStore((state) => state.title);
  const ownHeader = usePageTitleStore((state) => state.ownHeader);
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const handleNavClick = (path: string) => {
    navigate(path);
    setDrawerOpen(false);
  };

  const userInitials = (user?.nombre ?? "")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join("");

  const groups: { title: string; items: NavItem[] }[] = [
    { title: "Operación", items: [NAV_ITEMS[2], NAV_ITEMS[3]] },
    { title: "Datos", items: [NAV_ITEMS[1], NAV_ITEMS[4], NAV_ITEMS[5], NAV_ITEMS[6]] },
    {
      title: "Análisis",
      items: [NAV_ITEMS[7], ...(hasPermission(user, "usuarios.administrar") ? [NAV_ITEM_ADMIN] : [])],
    },
  ];

  const renderItem = (item: NavItem) => {
    const isActive =
      item.path === "/" ? location.pathname === "/" : location.pathname.startsWith(item.activePrefix ?? item.path);
    const Icon = item.icon;
    return (
      <button
        key={item.path}
        type="button"
        className={[styles.navItem, isActive ? styles.navItemActive : ""].filter(Boolean).join(" ")}
        onClick={() => handleNavClick(item.path)}
        aria-current={isActive ? "page" : undefined}
      >
        <Icon size={18} strokeWidth={1.75} />
        {item.label}
      </button>
    );
  };

  return (
    <div className={styles.shell}>
      <div
        className={[styles.overlay, drawerOpen ? styles.overlayVisible : ""].filter(Boolean).join(" ")}
        onClick={() => setDrawerOpen(false)}
      />

      <aside className={[styles.sidebar, drawerOpen ? styles.sidebarOpen : ""].filter(Boolean).join(" ")}>
        <Link to="/" className={styles.brand} aria-label="Ir a Inicio">
          <img src={logo} alt="Transportes Guerreros & Guerreros S.A.S." className={styles.brandLogo} />
        </Link>
        <nav className={styles.nav}>
          {groups.map((group) => (
            <div key={group.title} className={styles.group}>
              <div className={styles.groupTitle}>{group.title}</div>
              {group.items.map(renderItem)}
            </div>
          ))}
        </nav>
        <div className={styles.userCard}>
          <div className={styles.avatar} aria-hidden="true">{userInitials}</div>
          <div className={styles.userText}>
            <span className={styles.userName}>{user?.nombre}</span>
            <span className={styles.userRole}>{user?.roles?.[0] ?? "Usuario"}</span>
          </div>
          <button type="button" className={styles.logoutButton} onClick={handleLogout} aria-label="Cerrar sesión" title="Cerrar sesión">
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      <div className={styles.main}>
        <header className={styles.header}>
          <button
            type="button"
            className={styles.hamburger}
            onClick={() => setDrawerOpen((open) => !open)}
            aria-label="Abrir menú"
          >
            {drawerOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <span className={styles.pageTitle}>{title}</span>
        </header>
        <main className={styles.content}>
          <div className={styles.contentInner}>
            {!ownHeader && title && (
              <div className={styles.fallbackHeader}>
                <h1 className={styles.fallbackTitle}>{title}</h1>
                <div className={styles.fallbackGlow} aria-hidden="true" />
              </div>
            )}
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
