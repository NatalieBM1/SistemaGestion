import { ShieldAlert } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button, EmptyState } from "../components/ui";
import { usePageTitle } from "../store/pageTitleStore";

interface AccesoDenegadoState {
  permisoRequerido?: string;
  rutaOriginal?: string;
}

export function AccesoDenegado() {
  usePageTitle("Acceso denegado");
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state as AccesoDenegadoState | null) ?? null;

  return (
    <EmptyState
      icon={<ShieldAlert size={32} strokeWidth={1.5} />}
      title="No tienes acceso a esta sección"
      description={
        state?.permisoRequerido
          ? `Tu usuario no tiene el permiso requerido ('${state.permisoRequerido}') para ver esta página. Si crees que deberías tenerlo, contacta a un administrador.`
          : "Tu usuario no tiene permiso para ver esta página. Si crees que deberías tenerlo, contacta a un administrador."
      }
      action={
        <Button variant="primary" onClick={() => navigate("/")}>
          Volver al inicio
        </Button>
      }
    />
  );
}
