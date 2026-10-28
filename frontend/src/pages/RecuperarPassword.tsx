import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, CheckCircle, Lock, Mail, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";
import { authApi } from "../api/auth";
import { getApiErrorMessage } from "../api/errors";
import { Button, Input } from "../components/ui";
import logo from "../assets/Logo_Transportes.png";
import styles from "../styles/Login.module.css";
import propio from "../styles/RecuperarPassword.module.css";

// ── Paso 1: pedir el email ────────────────────────────────────────────────────
const emailSchema = z.object({
  email: z.string().min(1, "El correo es obligatorio.").email("Ingresa un correo válido."),
});
type EmailForm = z.infer<typeof emailSchema>;

// ── Paso 2: código + nueva contraseña ────────────────────────────────────────
const resetSchema = z
  .object({
    codigo: z
      .string()
      .length(6, "El código debe tener 6 dígitos.")
      .regex(/^\d{6}$/, "Solo se permiten números."),
    nueva_password: z.string().min(8, "La contraseña debe tener al menos 8 caracteres."),
    confirmar_password: z.string().min(1, "Confirma tu contraseña."),
  })
  .refine((d) => d.nueva_password === d.confirmar_password, {
    message: "Las contraseñas no coinciden.",
    path: ["confirmar_password"],
  });
type ResetForm = z.infer<typeof resetSchema>;

type Paso = "email" | "codigo" | "exito";

export function RecuperarPasswordPage() {
  const [paso, setPaso] = useState<Paso>("email");
  const [emailEnviado, setEmailEnviado] = useState("");
  const [serverError, setServerError] = useState<string | null>(null);

  // ── Formulario paso 1 ───────────────────────────────────────────────────────
  const formEmail = useForm<EmailForm>({ resolver: zodResolver(emailSchema) });

  const onEnviarEmail = async (values: EmailForm) => {
    setServerError(null);
    try {
      await authApi.forgotPassword(values.email);
      setEmailEnviado(values.email);
      setPaso("codigo");
    } catch (err) {
      setServerError(getApiErrorMessage(err, "No se pudo enviar el correo. Intenta de nuevo."));
    }
  };

  // ── Formulario paso 2 ───────────────────────────────────────────────────────
  const formReset = useForm<ResetForm>({ resolver: zodResolver(resetSchema) });

  const onResetPassword = async (values: ResetForm) => {
    setServerError(null);
    try {
      await authApi.resetPassword(emailEnviado, values.codigo, values.nueva_password);
      setPaso("exito");
    } catch (err) {
      setServerError(getApiErrorMessage(err, "No se pudo cambiar la contraseña."));
    }
  };

  return (
    <div className={styles.scene}>
      {/* fondo decorativo igual al Login */}
      <div className={styles.road} aria-hidden="true">
        <svg viewBox="0 0 1440 420" preserveAspectRatio="none">
          <defs>
            <linearGradient id="rec-road-fade" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0" stopColor="#2f5fe0" stopOpacity="0" />
              <stop offset="1" stopColor="#2f5fe0" stopOpacity="0.85" />
            </linearGradient>
          </defs>
          <g stroke="url(#rec-road-fade)" strokeWidth="1.6" fill="none">
            <path d="M720 0 L-200 420" /><path d="M720 0 L120 420" />
            <path d="M720 0 L420 420" /><path d="M720 0 L720 420" />
            <path d="M720 0 L1020 420" /><path d="M720 0 L1320 420" />
            <path d="M720 0 L1640 420" />
          </g>
          <g stroke="#2f5fe0" strokeOpacity="0.35" fill="none">
            <path d="M0 120 H1440" /><path d="M0 210 H1440" /><path d="M0 310 H1440" />
          </g>
        </svg>
      </div>

      <div className={`${styles.card} ${propio.cardAngosta}`}>
        {/* Columna izquierda: formulario */}
        <section className={styles.formCol} aria-labelledby="rec-titulo">
          {/* Volver al login */}
          <Link to="/login" className={propio.volver}>
            <ArrowLeft size={14} aria-hidden="true" />
            Volver al inicio de sesión
          </Link>

          <span className={styles.chip}>Sistema de Remisiones</span>
          <h1 id="rec-titulo" className={styles.title}>
            {paso === "email" && "Recuperar contraseña"}
            {paso === "codigo" && "Verifica tu identidad"}
            {paso === "exito" && "¡Listo!"}
          </h1>

          {/* ── Paso 1: email ── */}
          {paso === "email" && (
            <>
              <p className={styles.subtitle}>
                Ingresa el correo de tu cuenta y te enviaremos un código de verificación.
              </p>
              {serverError && (
                <div role="alert" className={styles.error}>{serverError}</div>
              )}
              <form
                className={styles.form}
                onSubmit={formEmail.handleSubmit(onEnviarEmail)}
                noValidate
              >
                <Input
                  label="Correo"
                  type="email"
                  autoComplete="email"
                  placeholder="usuario@empresa.com"
                  leftElement={<Mail size={16} aria-hidden="true" />}
                  error={formEmail.formState.errors.email?.message}
                  {...formEmail.register("email")}
                />
                <Button
                  type="submit"
                  variant="primary"
                  fullWidth
                  loading={formEmail.formState.isSubmitting}
                  className={styles.submit}
                >
                  {formEmail.formState.isSubmitting ? "Enviando…" : "Enviar código"}
                </Button>
              </form>
            </>
          )}

          {/* ── Paso 2: código + nueva contraseña ── */}
          {paso === "codigo" && (
            <>
              <p className={styles.subtitle}>
                Enviamos un código de 6 dígitos a{" "}
                <strong className={propio.emailDestacado}>{emailEnviado}</strong>.
                Ingrésalo junto a tu nueva contraseña.
              </p>
              {serverError && (
                <div role="alert" className={styles.error}>{serverError}</div>
              )}
              <form
                className={styles.form}
                onSubmit={formReset.handleSubmit(onResetPassword)}
                noValidate
              >
                <Input
                  label="Código de verificación"
                  type="text"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  placeholder="123456"
                  maxLength={6}
                  leftElement={<ShieldCheck size={16} aria-hidden="true" />}
                  error={formReset.formState.errors.codigo?.message}
                  {...formReset.register("codigo")}
                />
                <Input
                  label="Nueva contraseña"
                  type="password"
                  autoComplete="new-password"
                  placeholder="Mínimo 8 caracteres"
                  leftElement={<Lock size={16} aria-hidden="true" />}
                  error={formReset.formState.errors.nueva_password?.message}
                  {...formReset.register("nueva_password")}
                />
                <Input
                  label="Confirmar contraseña"
                  type="password"
                  autoComplete="new-password"
                  placeholder="Repite la contraseña"
                  leftElement={<Lock size={16} aria-hidden="true" />}
                  error={formReset.formState.errors.confirmar_password?.message}
                  {...formReset.register("confirmar_password")}
                />
                <Button
                  type="submit"
                  variant="primary"
                  fullWidth
                  loading={formReset.formState.isSubmitting}
                  className={styles.submit}
                >
                  {formReset.formState.isSubmitting ? "Cambiando…" : "Cambiar contraseña"}
                </Button>

                <button
                  type="button"
                  className={propio.reenviar}
                  onClick={() => {
                    setServerError(null);
                    setPaso("email");
                  }}
                >
                  ¿No recibiste el código? Volver a intentar
                </button>
              </form>
            </>
          )}

          {/* ── Paso 3: éxito ── */}
          {paso === "exito" && (
            <div className={propio.exito}>
              <CheckCircle size={52} className={propio.exitoIcon} aria-hidden="true" />
              <p className={propio.exitoTexto}>
                Tu contraseña se actualizó correctamente.
              </p>
              <Link to="/login">
                <Button variant="primary" fullWidth className={styles.submit}>
                  Ir al inicio de sesión
                </Button>
              </Link>
            </div>
          )}
        </section>

        {/* Columna derecha: logo */}
        <aside className={styles.brand}>
          <img
            src={logo}
            alt="Transportes Guerreros & Guerreros S.A.S."
            className={styles.logo}
          />
          <p className={styles.tagline}>Gestión de remisiones y facturación</p>
        </aside>
      </div>
    </div>
  );
}
