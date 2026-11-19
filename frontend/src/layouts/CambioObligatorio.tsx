import { KeyRound } from "lucide-react";
import { Button } from "../components/ui";
import { useAuthStore } from "../store/authStore";
import styles from "./MainLayout.module.css";
import { FormularioCambioContrasena } from "./MenuUsuario";

/** Pantalla que reemplaza la app mientras el usuario tenga pendiente el
 * cambio obligatorio de contraseña (cuenta nueva en producción o contraseña
 * restablecida por un administrador). Solo deja cambiarla o cerrar sesión. */
export function CambioObligatorio({ onCerrarSesion }: { onCerrarSesion: () => void }) {
  const user = useAuthStore((s) => s.user);
  return (
    <div className={styles.cambioObligatorio}>
      <main className={styles.cambioObligatorioTarjeta} aria-labelledby="titulo-cambio-obligatorio">
        <div className={styles.cambioObligatorioIcono} aria-hidden="true">
          <KeyRound size={22} />
        </div>
        <h1 id="titulo-cambio-obligatorio" className={styles.cambioObligatorioTitulo}>
          Cambia tu contraseña
        </h1>
        <p className={styles.cambioObligatorioTexto}>
          {user?.nombre ? `${user.nombre}, antes` : "Antes"} de continuar debes cambiar la contraseña que te asignaron.
          Escribe la contraseña actual y elige una nueva que solo tú conozcas.
        </p>
        <FormularioCambioContrasena
          onListo={() => undefined}
          acciones={(guardando) => (
            <>
              <Button type="button" variant="ghost" onClick={onCerrarSesion}>
                Cerrar sesión
              </Button>
              <Button type="submit" variant="primary" loading={guardando}>
                Guardar contraseña
              </Button>
            </>
          )}
        />
      </main>
    </div>
  );
}
