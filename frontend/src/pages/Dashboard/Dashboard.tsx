import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Building2, Car, FileWarning, Plus, Receipt, Truck } from "lucide-react";
import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../../api/client";
import { listRemisiones } from "../../api/remisiones";
import { Button } from "../../components/ui";
import { formatMoney } from "../../lib/format";
import { useAuthStore } from "../../store/authStore";
import { usePageTitle } from "../../store/pageTitleStore";

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

interface StatCardProps {
  icon: ReactNode;
  label: string;
  value: ReactNode;
  tone?: "default" | "warning";
  hint?: string;
}

function StatCard({ icon, label, value, tone = "default", hint }: StatCardProps) {
  return (
    <div
      style={{
        background: "var(--bg-surface)",
        border: `1px solid ${tone === "warning" ? "var(--warning)" : "var(--border)"}`,
        borderRadius: "var(--radius-md)",
        padding: "var(--space-4)",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-2)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", color: tone === "warning" ? "var(--warning)" : "var(--accent)" }}>
        {icon}
        <span style={{ fontSize: "var(--text-caption)", color: "var(--text-secondary)", fontWeight: 500 }}>{label}</span>
      </div>
      <div style={{ fontSize: "var(--text-title)", fontWeight: 600, color: "var(--text-primary)" }}>{value}</div>
      {hint && <div style={{ fontSize: "var(--text-caption)", color: "var(--text-secondary)" }}>{hint}</div>}
    </div>
  );
}

export function Dashboard() {
  usePageTitle("Inicio");
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);

  const desdeMes = primerDiaDelMes();
  const hasta = hoyISO();

  const { data: remisionesMes } = useQuery({
    queryKey: ["dashboard-remisiones-mes", desdeMes, hasta],
    queryFn: () => listRemisiones({ page: 1, page_size: 1, desde: desdeMes, hasta }),
  });

  const { data: noFacturadas } = useQuery({
    queryKey: ["dashboard-no-facturadas"],
    queryFn: () => listRemisiones({ page: 1, page_size: 1, estado_facturacion: "NO_FACTURADA" }),
  });

  const { data: facturadaParcial } = useQuery({
    queryKey: ["dashboard-facturada-parcial"],
    queryFn: () => listRemisiones({ page: 1, page_size: 1, estado_facturacion: "FACTURADA_PARCIAL" }),
  });

  const { data: resumenFacturado } = useQuery({
    queryKey: ["dashboard-resumen-facturado", desdeMes, hasta],
    queryFn: async () => {
      const { data } = await apiClient.get("/api/facturas/resumen", { params: { desde: desdeMes, hasta } });
      return data as { valor_total_facturado: string; cantidad_facturaciones: number };
    },
  });

  const { data: terceros } = useQuery({
    queryKey: ["dashboard-terceros"],
    queryFn: async () => {
      const { data } = await apiClient.get("/api/terceros", { params: { page_size: 1 } });
      return data as { total: number };
    },
  });

  const { data: activos } = useQuery({
    queryKey: ["dashboard-activos"],
    queryFn: async () => {
      const { data } = await apiClient.get("/api/activos", { params: { page_size: 1 } });
      return data as { total: number };
    },
  });

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          marginBottom: "var(--space-6)",
          flexWrap: "wrap",
          gap: "var(--space-4)",
        }}
      >
        <div>
          <p style={{ color: "var(--text-secondary)", margin: "0 0 var(--space-1)", fontSize: "var(--text-caption)" }}>
            {fechaDeHoyLarga()}
          </p>
          <h1 style={{ margin: 0 }}>{primerNombre(user?.nombre) ? `Hola, ${primerNombre(user?.nombre)}` : "Inicio"}</h1>
          <p style={{ color: "var(--text-secondary)", margin: "var(--space-1) 0 0" }}>
            Este es el resumen del sistema, actualizado en tiempo real.
          </p>
        </div>
        <Button variant="primary" leftIcon={<Plus size={16} />} onClick={() => navigate("/remisiones/nueva")}>
          Nueva remisión
        </Button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "var(--space-4)" }}>
        <StatCard
          icon={<Truck size={18} strokeWidth={1.75} />}
          label="Remisiones este mes"
          value={remisionesMes?.total ?? "—"}
        />
        <StatCard
          icon={<FileWarning size={18} strokeWidth={1.75} />}
          label="No facturadas"
          value={noFacturadas?.total ?? "—"}
          hint="Pendientes de iniciar facturación"
        />
        <StatCard
          icon={<AlertTriangle size={18} strokeWidth={1.75} />}
          label="Facturadas parcialmente"
          value={facturadaParcial?.total ?? "—"}
          tone={(facturadaParcial?.total ?? 0) > 0 ? "warning" : "default"}
          hint="Con saldo pendiente de cobro"
        />
        <StatCard
          icon={<Receipt size={18} strokeWidth={1.75} />}
          label="Facturado este mes"
          value={resumenFacturado ? formatMoney(resumenFacturado.valor_total_facturado) : "—"}
          hint={resumenFacturado ? `${resumenFacturado.cantidad_facturaciones} facturación(es) activa(s)` : undefined}
        />
        <StatCard icon={<Building2 size={18} strokeWidth={1.75} />} label="Terceros registrados" value={terceros?.total ?? "—"} />
        <StatCard icon={<Car size={18} strokeWidth={1.75} />} label="Activos registrados" value={activos?.total ?? "—"} />
      </div>
    </div>
  );
}
