import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { RequirePermission } from "./components/RequirePermission";
import { CatalogosLayout } from "./layouts/CatalogosLayout";
import { MainLayout } from "./layouts/MainLayout";
import { FormasPagoPage } from "./pages/catalogos/FormasPagoPage";
import { PrefijosFacturaPage } from "./pages/catalogos/PrefijosFacturaPage";
import { PrefijosPage } from "./pages/catalogos/PrefijosPage";
import { ProductosPage } from "./pages/catalogos/ProductosPage";
import { TiposServicioPage } from "./pages/catalogos/TiposServicioPage";
import { TiposTerceroPage } from "./pages/catalogos/TiposTerceroPage";
import { UnidadesMedidaPage } from "./pages/catalogos/UnidadesMedidaPage";
import { LoginPage } from "./pages/Login";
import { RecuperarPasswordPage } from "./pages/RecuperarPassword";
import { AccesoDenegado } from "./pages/AccesoDenegado";
import { CargasExcel } from "./pages/Facturas/CargasExcel";
import { DetalleFactura } from "./pages/Facturas/DetalleFactura";
import { ListadoFacturas } from "./pages/Facturas/ListadoFacturas";
import { ImprimirRemision } from "./pages/Remisiones/ImprimirRemision";
import { ListadoRemisiones } from "./pages/Remisiones/ListadoRemisiones";
import { RemisionForm } from "./pages/Remisiones/RemisionForm";
import { ListadoTerceros } from "./pages/Terceros/ListadoTerceros";
import { ListadoUbicaciones } from "./pages/Ubicaciones/ListadoUbicaciones";
import { ListadoActivos } from "./pages/Activos/ListadoActivos";
import { Reportes } from "./pages/Reportes/Reportes";
import { Usuarios } from "./pages/Admin/Usuarios";
import { Roles } from "./pages/Admin/Roles";
import { RolDetalle } from "./pages/Admin/RolDetalle";
import { Dashboard } from "./pages/Dashboard/Dashboard";

export function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/recuperar-password" element={<RecuperarPasswordPage />} />

      {/* Ruta de impresión: fuera de MainLayout a propósito (sin sidebar/
          header) para que @media print no tenga que pelear con ese CSS. */}
      <Route
        path="/remisiones/:id/imprimir"
        element={
          <ProtectedRoute>
            <ImprimirRemision />
          </ProtectedRoute>
        }
      />

      <Route
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/acceso-denegado" element={<AccesoDenegado />} />

        <Route path="/catalogos" element={<CatalogosLayout />}>
          <Route index element={<Navigate to="/catalogos/prefijos" replace />} />
          <Route path="prefijos" element={<PrefijosPage />} />
          <Route path="formas_pago" element={<FormasPagoPage />} />
          <Route path="tipos_servicio" element={<TiposServicioPage />} />
          <Route path="productos" element={<ProductosPage />} />
          <Route path="unidades_medida" element={<UnidadesMedidaPage />} />
          <Route path="prefijos_factura" element={<PrefijosFacturaPage />} />
          <Route path="tipos_tercero" element={<TiposTerceroPage />} />
        </Route>

        <Route path="/remisiones" element={<ListadoRemisiones />} />
        <Route path="/remisiones/nueva" element={<RemisionForm />} />
        <Route path="/remisiones/:id" element={<RemisionForm />} />
        <Route path="/facturas" element={<ListadoFacturas />} />
        <Route path="/facturas/cargas-excel" element={<CargasExcel />} />
        <Route path="/facturas/:numeroFactura" element={<DetalleFactura />} />
        <Route path="/terceros" element={<ListadoTerceros />} />
        <Route path="/ubicaciones" element={<ListadoUbicaciones />} />
        <Route path="/activos" element={<ListadoActivos />} />
        <Route path="/reportes" element={<Reportes />} />

        <Route
          path="/admin/usuarios"
          element={
            <RequirePermission permiso="usuarios.administrar">
              <Usuarios />
            </RequirePermission>
          }
        />
        <Route
          path="/admin/roles"
          element={
            <RequirePermission permiso="usuarios.administrar">
              <Roles />
            </RequirePermission>
          }
        />
        <Route
          path="/admin/roles/:id"
          element={
            <RequirePermission permiso="usuarios.administrar">
              <RolDetalle />
            </RequirePermission>
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
