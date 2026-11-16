import { useMutation } from "@tanstack/react-query";
import { ChevronUp, Eye, EyeOff, KeyRound, LogOut } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { authApi } from "../api/auth";
import { getApiErrorMessage } from "../api/errors";
import { Button, Input, Modal, useToast } from "../components/ui";
import { useAuthStore } from "../store/authStore";
import styles from "./MainLayout.module.css";

/** Tarjeta del usuario al pie del menú lateral. Al hacer clic abre un menú
 * con "Cambiar contraseña" y "Cerrar sesión". */
export function MenuUsuario({
  onCerrarSesion,
  onAbrirVentana,
}: {
  onCerrarSesion: () => void;
  /** Se llama al abrir "Cambiar contraseña" (el layout cierra el menú lateral
   * en celular, cuyo fondo quedaría encima de la ventana). */
  onAbrirVentana?: () => void;
}) {
  const user = useAuthStore((state) => state.user);
  const [abierto, setAbierto] = useState(false);
  const [cambiando, setCambiando] = useState(false);
  const contenedor = useRef<HTMLDivElement>(null);
  const boton = useRef<HTMLButtonElement>(null);
  const idMenu = useId();

  const iniciales = (user?.nombre ?? "")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join("");

  useEffect(() => {
    if (!abierto) return;
    const fuera = (e: MouseEvent) => {
      if (contenedor.current && !contenedor.current.contains(e.target as Node)) setAbierto(false);
    };
    const tecla = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setAbierto(false);
        boton.current?.focus();
      }
    };
    document.addEventListener("mousedown", fuera);
    document.addEventListener("keydown", tecla);
    // Lleva el foco a la primera opción para poder usar el teclado.
    contenedor.current?.querySelector<HTMLButtonElement>('[role="menuitem"]')?.focus();
    return () => {
      document.removeEventListener("mousedown", fuera);
      document.removeEventListener("keydown", tecla);
    };
  }, [abierto]);

  const moverFoco = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
    e.preventDefault();
    const items = [...(contenedor.current?.querySelectorAll<HTMLButtonElement>('[role="menuitem"]') ?? [])];
    const i = items.indexOf(document.activeElement as HTMLButtonElement);
    const sig = e.key === "ArrowDown" ? (i + 1) % items.length : (i - 1 + items.length) % items.length;
    items[sig]?.focus();
  };

  return (
    <div className={styles.userMenuWrap} ref={contenedor}>
      {abierto && (
        <div id={idMenu} className={styles.userMenu} role="menu" aria-label="Opciones de la cuenta" onKeyDown={moverFoco}>
          <button
            type="button"
            role="menuitem"
            className={styles.userMenuItem}
            onClick={() => {
              setAbierto(false);
              onAbrirVentana?.();
              setCambiando(true);
            }}
          >
            <KeyRound size={16} aria-hidden="true" />
            Cambiar contraseña
          </button>
          <button type="button" role="menuitem" className={styles.userMenuItem} onClick={onCerrarSesion}>
            <LogOut size={16} aria-hidden="true" />
            Cerrar sesión
          </button>
        </div>
      )}
      <button
        ref={boton}
        type="button"
        className={styles.userCard}
        onClick={() => setAbierto((a) => !a)}
        aria-haspopup="menu"
        aria-expanded={abierto}
        aria-controls={abierto ? idMenu : undefined}
        title="Opciones de la cuenta"
      >
        <span className={styles.avatar} aria-hidden="true">
          {iniciales}
        </span>
        <span className={styles.userText}>
          <span className={styles.userName}>{user?.nombre}</span>
          <span className={styles.userRole}>{user?.roles?.[0] ?? "Usuario"}</span>
        </span>
        <ChevronUp size={16} className={[styles.userChevron, abierto ? styles.userChevronAbierto : ""].join(" ")} aria-hidden="true" />
      </button>
      <CambiarContrasenaModal abierto={cambiando} onCerrar={() => setCambiando(false)} />
    </div>
  );
}

interface ValoresCambio {
  actual: string;
  nueva: string;
  confirmar: string;
}

function CambiarContrasenaModal({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const toast = useToast();
  const setTokens = useAuthStore((s) => s.setTokens);
  const [error, setError] = useState<string | null>(null);
  const [ver, setVer] = useState(false);
  const {
    register,
    handleSubmit,
    reset,
    getValues,
    formState: { errors },
  } = useForm<ValoresCambio>({ defaultValues: { actual: "", nueva: "", confirmar: "" } });

  const mutation = useMutation({
    mutationFn: (v: ValoresCambio) => authApi.cambiarPassword(v.actual, v.nueva),
    onSuccess: ({ data }) => {
      setTokens(data.access_token, data.refresh_token);
      toast.success("Tu contraseña se actualizó. Las sesiones abiertas en otros equipos se cerraron.");
      cerrar();
    },
    onError: (err) => setError(getApiErrorMessage(err, "No se pudo cambiar la contraseña.")),
  });

  const cerrar = () => {
    setError(null);
    setVer(false);
    reset();
    onCerrar();
  };

  const ojo = (
    <button
      type="button"
      className={styles.verClave}
      onClick={() => setVer((v) => !v)}
      aria-label={ver ? "Ocultar contraseñas" : "Mostrar contraseñas"}
      title={ver ? "Ocultar contraseñas" : "Mostrar contraseñas"}
    >
      {ver ? <EyeOff size={16} /> : <Eye size={16} />}
    </button>
  );
  const tipo = ver ? "text" : "password";

  return (
    <Modal
      open={abierto}
      onClose={cerrar}
      title="Cambiar contraseña"
      size="sm"
      footer={
        <>
          <Button type="button" variant="ghost" onClick={cerrar}>
            Cancelar
          </Button>
          <Button type="submit" form="cambiar-contrasena-form" variant="primary" loading={mutation.isPending}>
            Guardar contraseña
          </Button>
        </>
      }
    >
      <form
        id="cambiar-contrasena-form"
        onSubmit={handleSubmit((v) => {
          setError(null);
          mutation.mutate(v);
        })}
        className={styles.formCambio}
        noValidate
      >
        {error && (
          <div className={styles.formCambioError} role="alert">
            {error}
          </div>
        )}
        <Input
          label="Contraseña actual"
          type={tipo}
          autoComplete="current-password"
          required
          rightElement={ojo}
          error={errors.actual?.message}
          {...register("actual", { required: "Escribe tu contraseña actual." })}
        />
        <Input
          label="Nueva contraseña"
          type={tipo}
          autoComplete="new-password"
          required
          hint="Mínimo 8 caracteres."
          error={errors.nueva?.message}
          {...register("nueva", {
            required: "Escribe la nueva contraseña.",
            minLength: { value: 8, message: "La nueva contraseña debe tener al menos 8 caracteres." },
            validate: (v) => v !== getValues("actual") || "La nueva contraseña debe ser diferente de la actual.",
          })}
        />
        <Input
          label="Confirmar contraseña"
          type={tipo}
          autoComplete="new-password"
          required
          error={errors.confirmar?.message}
          {...register("confirmar", {
            required: "Repite la nueva contraseña.",
            validate: (v) => v === getValues("nueva") || "Las contraseñas no coinciden.",
          })}
        />
        <p className={styles.formCambioNota}>
          Al guardar, se cierran las sesiones abiertas en otros equipos. En este equipo sigues trabajando.
        </p>
      </form>
    </Modal>
  );
}
