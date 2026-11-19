import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { activarUsuarioHistorico, type UsuarioAdmin } from "../../api/admin";
import { getApiErrorMessage } from "../../api/errors";
import { BotonCopiar, Button, Input, Modal, Select } from "../../components/ui";
import styles from "./ActivarHistoricoModal.module.css";

interface Valores {
  email: string;
  rol: string;
}

/** Activa un usuario histórico (creador de remisiones del Excel, sin acceso)
 * como cuenta real. El servidor genera una contraseña temporal aleatoria que se
 * muestra aquí una sola vez; al entrar, la persona debe cambiarla. */
export function ActivarHistoricoModal({ usuario, onClose }: { usuario: UsuarioAdmin | null; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  // Solo en el estado de esta ventana: no va a la caché de consultas.
  const [temporal, setTemporal] = useState<string | null>(null);
  const [cuenta, setCuenta] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<Valores>({ defaultValues: { email: "", rol: "Operador" } });

  const mutation = useMutation({
    mutationFn: (v: Valores) =>
      activarUsuarioHistorico({ identificacion: usuario!.identificacion ?? "", email: v.email, rol: v.rol }),
    onSuccess: (r) => {
      setTemporal(r.password_temporal);
      setCuenta(r.usuario.email);
      queryClient.invalidateQueries({ queryKey: ["usuarios-admin"] });
    },
    onError: (err) => setError(getApiErrorMessage(err, "No se pudo activar la cuenta.")),
  });

  const cerrar = () => {
    setTemporal(null);
    setCuenta(null);
    setError(null);
    reset();
    onClose();
  };

  return (
    <Modal
      open={Boolean(usuario)}
      onClose={cerrar}
      title="Activar cuenta"
      size="sm"
      footer={
        temporal ? (
          <Button type="button" variant="primary" onClick={cerrar}>
            Listo
          </Button>
        ) : (
          <>
            <Button type="button" variant="ghost" onClick={cerrar}>
              Cancelar
            </Button>
            <Button type="submit" form="activar-historico-form" variant="primary" loading={mutation.isPending}>
              Activar cuenta
            </Button>
          </>
        )
      }
    >
      {temporal ? (
        <div className={styles.resultado}>
          <p className={styles.texto}>
            Cuenta activada para <strong>{usuario?.nombre}</strong> ({cuenta}). Conserva sus remisiones.
          </p>
          <div className={styles.clave}>
            <span className={styles.etiqueta}>Contraseña temporal</span>
            <code className={styles.valor} data-testid="password-temporal">
              {temporal}
            </code>
            <BotonCopiar texto={temporal} que="la contraseña temporal" />
          </div>
          <p className={styles.aviso} role="alert">
            Se muestra <strong>una sola vez</strong> y no queda guardada. Entrégala a la persona por un canal seguro.
            Al entrar, el sistema le pedirá cambiarla antes de usar cualquier otra pantalla.
          </p>
        </div>
      ) : (
        <form
          id="activar-historico-form"
          className={styles.formulario}
          onSubmit={handleSubmit((v) => {
            setError(null);
            mutation.mutate(v);
          })}
          noValidate
        >
          {error && (
            <div className={styles.error} role="alert">
              {error}
            </div>
          )}
          <p className={styles.texto}>
            <strong>{usuario?.nombre}</strong> creó remisiones en el Excel y hoy no tiene acceso. Al activarla, la cuenta
            queda con sus remisiones; el sistema genera una contraseña temporal que verás una sola vez.
          </p>
          <Input label="Identificación" value={usuario?.identificacion ?? ""} readOnly />
          <Input
            label="Correo"
            type="email"
            autoComplete="off"
            required
            error={errors.email?.message}
            {...register("email", {
              required: "Escribe el correo de la persona.",
              pattern: { value: /^[^@\s]+@[^@\s]+\.[^@\s]+$/, message: "El correo no es válido." },
            })}
          />
          <Select label="Rol" {...register("rol")}>
            <option value="Operador">Operador</option>
            <option value="Administrador">Administrador</option>
            <option value="Solo Consulta">Solo Consulta</option>
          </Select>
        </form>
      )}
    </Modal>
  );
}
