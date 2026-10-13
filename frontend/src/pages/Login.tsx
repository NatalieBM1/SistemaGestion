import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff, Lock, Mail } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";
import { getApiErrorMessage } from "../api/errors";
import { Button, Input } from "../components/ui";
import { useAuthStore } from "../store/authStore";
import logo from "../assets/Logo_Transportes.png";
import truck from "../assets/truck_only.png";
import styles from "../styles/Login.module.css";

const loginSchema = z.object({
  email: z.string().min(1, "El email es obligatorio.").email("Ingresa un email válido."),
  password: z.string().min(1, "La contraseña es obligatoria."),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export function LoginPage() {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const loadUserFromMe = useAuthStore((state) => state.loadUserFromMe);
  const [serverError, setServerError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (values: LoginFormValues) => {
    setServerError(null);
    try {
      await login(values.email, values.password);
      await loadUserFromMe();
      navigate("/", { replace: true });
    } catch (error) {
      setServerError(getApiErrorMessage(error, "No se pudo iniciar sesión."));
    }
  };

  return (
    <div className={styles.scene}>
      <div className={styles.road} aria-hidden="true">
        <svg viewBox="0 0 1440 420" preserveAspectRatio="none">
          <defs>
            <linearGradient id="login-road-fade" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0" stopColor="#2f5fe0" stopOpacity="0" />
              <stop offset="1" stopColor="#2f5fe0" stopOpacity="0.85" />
            </linearGradient>
          </defs>
          <g stroke="url(#login-road-fade)" strokeWidth="1.6" fill="none">
            <path d="M720 0 L-200 420" />
            <path d="M720 0 L120 420" />
            <path d="M720 0 L420 420" />
            <path d="M720 0 L720 420" />
            <path d="M720 0 L1020 420" />
            <path d="M720 0 L1320 420" />
            <path d="M720 0 L1640 420" />
          </g>
          <g stroke="#2f5fe0" strokeOpacity="0.35" fill="none">
            <path d="M0 120 H1440" />
            <path d="M0 210 H1440" />
            <path d="M0 310 H1440" />
          </g>
        </svg>
      </div>
      <img src={truck} alt="" aria-hidden="true" className={styles.truck} />

      <div className={styles.card}>
        <section className={styles.formCol} aria-labelledby="login-titulo">
          <span className={styles.chip}>Sistema de Remisiones</span>
          <h1 id="login-titulo" className={styles.title}>
            Iniciar sesión
          </h1>
          <p className={styles.subtitle}>Ingresa con tu cuenta para gestionar remisiones</p>

          {serverError && (
            <div role="alert" className={styles.error}>
              {serverError}
            </div>
          )}

          <form className={styles.form} onSubmit={handleSubmit(onSubmit)} noValidate>
            <Input
              label="Correo"
              type="email"
              autoComplete="username"
              error={errors.email?.message}
              placeholder="usuario@empresa.com"
              leftElement={<Mail size={16} aria-hidden="true" />}
              {...register("email")}
            />
            <Input
              label="Contraseña"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              error={errors.password?.message}
              placeholder="••••••••"
              leftElement={<Lock size={16} aria-hidden="true" />}
              rightElement={
                <button
                  type="button"
                  className={styles.toggle}
                  onClick={() => setShowPassword((current) => !current)}
                  aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              }
              {...register("password")}
            />
            <Button type="submit" variant="primary" fullWidth loading={isSubmitting} className={styles.submit}>
              {isSubmitting ? "Ingresando…" : "Iniciar sesión"}
            </Button>
          </form>
        </section>

        <aside className={styles.brand}>
          <img src={logo} alt="Transportes Guerreros & Guerreros S.A.S." className={styles.logo} />
          <p className={styles.tagline}>Gestión de remisiones y facturación</p>
        </aside>
      </div>
    </div>
  );
}
