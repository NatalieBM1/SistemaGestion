import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  BarChart3,
  Building2,
  Car,
  FileWarning,
  Plus,
  Receipt,
  Truck,
} from "lucide-react";
import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../../api/client";
import { listRemisiones } from "../../api/remisiones";
import { Button } from "../../components/ui";
import { formatMoney } from "../../lib/format";
import { useAuthStore } from "../../store/authStore";
import { usePageTitle } from "../../store/pageTitleStore";
import styles from "./Dashboard.module.css";

const FORMATO_FECHA = new Intl.DateTimeFormat("es-CO", {
  weekday: "long",
  day: "numeric",
  month: "long",
  year: "numeric",
});

function fechaDeHoyLarga(): string {
  const texto = FORMATO_FECHA.format(new Date());
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

function primerNombre(nombreCompleto: string | undefined): string {
  if (!nombreCompleto) return "";
  return nombreCompleto.split(" ")[0];
}

function primerDiaDelMes(): string {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10);
}

function hoyISO(): string {
  return new Date().toISOString().slice(0, 10);
}

type Tone = "default" | "warning" | "success" | "money";

interface StatCardProps {
  icon: ReactNode;
  label: string;
  value: ReactNode;
  tone?: Tone;
  hint?: string;
  showAlert?: boolean;
  progressPct?: number;
}

const toneCard: Record<Tone, string>  = {
  default: styles.cardDefault,
  warning: styles.cardWarning,
  success: styles.cardSuccess,
  money:   styles.cardMoney,
};
const toneIcon: Record<Tone, string> = {
  default: styles.iconDefault,
  warning: styles.iconWarning,
  success: styles.iconSuccess,
  money:   styles.iconMoney,
};

function StatCard({ icon, label, value, tone = "default", hint, showAlert, progressPct }: StatCardProps) {
  return (
    <div className={`${styles.card} ${toneCard[tone]}`}>
      {showAlert && <span className={styles.alertDot} aria-hidden="true" />}
      <div className={`${styles.iconWrap} ${toneIcon[tone]}`}>{icon}</div>
      <div>
        <div className={styles.cardLabel}>{label}</div>
        <div className={styles.cardValue}>{value}</div>
        {hint && <div className={styles.cardHint}>{hint}</div>}
      </div>
      {progressPct !== undefined && (
        <div className={styles.progress}>
          <div className={styles.progressTrack}>
            <div
              className={styles.progressFill}
              style={{ width: `${Math.min(progressPct, 100)}%` }}
              aria-hidden="true"
            />
          </div>
        </div>
      )}
    </div>
  );
}

interface QuickAction {
  label: string;
  icon: ReactNode;
  path: string;
}

export function Dashboard() {
  usePageTitle("Inicio");
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);

  const desdeMes = primerDiaDelMes();
  const hasta    = hoyISO();

  const { data: remisionesMes } = useQuery({
    queryKey: ["dashboard-remisiones-mes", desdeMes, hasta],
    queryFn:  () => listRemisiones({ page: 1, page_size: 1, desde: desdeMes, hasta }),
  });

  const { data: noFacturadas } = useQuery({
    queryKey: ["dashboard-no-facturadas"],
    queryFn:  () => listRemisiones({ page: 1, page_size: 1, estado_facturacion: "NO_FACTURADA" }),
  });

  const { data: facturadaParcial } = useQuery({
    queryKey: ["dashboard-facturada-parcial"],
    queryFn:  () => listRemisiones({ page: 1, page_size: 1, estado_facturacion: "FACTURADA_PARCIAL" }),
  });

  const { data: resumenFacturado } = useQuery({
    queryKey: ["dashboard-resumen-facturado", desdeMes, hasta],
    queryFn:  async () => {
      const { data } = await apiClient.get("/api/facturas/resumen", {
        params: { desde: desdeMes, hasta },
      });
      return data as { valor_total_facturado: string; cantidad_facturaciones: number };
    },
  });

  const { data: terceros } = useQuery({
    queryKey: ["dashboard-terceros"],
    queryFn:  async () => {
      const { data } = await apiClient.get("/api/terceros", { params: { page_size: 1 } });
      return data as { total: number };
    },
  });

  const { data: activos } = useQuery({
    queryKey: ["dashboard-activos"],
    queryFn:  async () => {
      const { data } = await apiClient.get("/api/activos", { params: { page_size: 1 } });
      return data as { total: number };
    },
  });

  // Porcentaje de remisiones pendientes de facturar respecto al mes
  const totalMes    = remisionesMes?.total ?? 0;
  const pendientes  = (noFacturadas?.total ?? 0) + (facturadaParcial?.total ?? 0);
  const progPct     = totalMes > 0 ? ((totalMes - pendientes) / totalMes) * 100 : 0;

  const quickActions: QuickAction[] = [
    { label: "Nueva remisión",   icon: <Plus size={18} />,      path: "/remisiones/nueva" },
    { label: "Ver remisiones",   icon: <Truck size={18} />,     path: "/remisiones" },
    { label: "Facturación",      icon: <Receipt size={18} />,   path: "/facturas" },
    { label: "Reportes",         icon: <BarChart3 size={18} />, path: "/reportes" },
    { label: "Terceros",         icon: <Building2 size={18} />, path: "/terceros" },
    { label: "Activos",          icon: <Car size={18} />,       path: "/activos" },
  ];

  return (
    <div>
      {/* Encabezado */}
      <div className={styles.hero}>
        <div className={styles.heroText}>
          <p className={styles.heroDate}>{fechaDeHoyLarga()}</p>
          <h1 className={styles.heroTitle}>
            {primerNombre(user?.nombre) ? `Hola, ${primerNombre(user?.nombre)} 👋` : "Inicio"}
          </h1>
          <p className={styles.heroSub}>
            Resumen del sistema · actualizado en tiempo real
          </p>
        </div>
        <Button
          variant="primary"
          leftIcon={<Plus size={16} />}
          onClick={() => navigate("/remisiones/nueva")}
        >
          Nueva remisión
        </Button>
      </div>

      {/* KPIs */}
      <div className={styles.grid}>
        <StatCard
          icon={<Truck size={20} strokeWidth={1.75} />}
          label="Remisiones este mes"
          value={remisionesMes?.total ?? "—"}
          hint={`Hasta el ${hasta.split("-").reverse().join("/")}`}
          progressPct={progPct}
        />
        <StatCard
          icon={<FileWarning size={20} strokeWidth={1.75} />}
          label="Sin facturar"
          value={noFacturadas?.total ?? "—"}
          hint="Pendientes de iniciar facturación"
          tone={(noFacturadas?.total ?? 0) > 0 ? "warning" : "default"}
          showAlert={(noFacturadas?.total ?? 0) > 0}
        />
        <StatCard
          icon={<AlertTriangle size={20} strokeWidth={1.75} />}
          label="Facturadas parcialmente"
          value={facturadaParcial?.total ?? "—"}
          hint="Con saldo pendiente de cobro"
          tone={(facturadaParcial?.total ?? 0) > 0 ? "warning" : "default"}
          showAlert={(facturadaParcial?.total ?? 0) > 0}
        />
        <StatCard
          icon={<Receipt size={20} strokeWidth={1.75} />}
          label="Facturado este mes"
          value={
            resumenFacturado
              ? formatMoney(resumenFacturado.valor_total_facturado)
              : "—"
          }
          hint={
            resumenFacturado
              ? `${resumenFacturado.cantidad_facturaciones} facturación(es)`
              : undefined
          }
          tone="money"
        />
        <StatCard
          icon={<Building2 size={20} strokeWidth={1.75} />}
          label="Terceros registrados"
          value={terceros?.total ?? "—"}
          tone="success"
        />
        <StatCard
          icon={<Car size={20} strokeWidth={1.75} />}
          label="Activos registrados"
          value={activos?.total ?? "—"}
          tone="success"
        />
      </div>

      {/* Acciones rápidas */}
      <div className={styles.section}>
        <p className={styles.sectionTitle}>Acciones rápidas</p>
        <div className={styles.quickGrid}>
          {quickActions.map((a) => (
            <button
              key={a.path}
              type="button"
              className={styles.quickCard}
              onClick={() => navigate(a.path)}
            >
              <span className={styles.quickIcon}>{a.icon}</span>
              <span className={styles.quickLabel}>{a.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
