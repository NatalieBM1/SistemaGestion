const OPCIONES = [10, 25, 50, 100];

interface SelectorFilasPorPaginaProps {
  value: number;
  onChange: (value: number) => void;
}

/** Selector de filas por página (10/25/50/100), reutilizado en todas las
 * listas paginadas. Mismo componente en todas partes — no lo dupliques. */
export function SelectorFilasPorPagina({ value, onChange }: SelectorFilasPorPaginaProps) {
  return (
    <label style={{ display: "flex", alignItems: "center", gap: "var(--space-1)", fontSize: "var(--text-caption)", color: "var(--text-secondary)" }}>
      Filas por página
      <select
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{ border: "none", background: "transparent", color: "var(--accent)", font: "inherit", fontWeight: 500, cursor: "pointer" }}
      >
        {OPCIONES.map((n) => (
          <option key={n} value={n}>
            {n}
          </option>
        ))}
      </select>
    </label>
  );
}

/** "1–25 de 1.000" — si no hay registros, "0 de 0". */
export function rangoRegistros(page: number, pageSize: number, total: number): string {
  if (total === 0) return "0 de 0";
  const desde = (page - 1) * pageSize + 1;
  const hasta = Math.min(page * pageSize, total);
  return `${desde}–${hasta} de ${total.toLocaleString("es-CO")}`;
}

/** Recuerda la cantidad de filas por página elegida, por lista, en
 * localStorage — falla en silencio si no hay almacenamiento disponible
 * (privado, bloqueado, etc.), nunca rompe la pantalla. */
export function leerFilasPorPaginaGuardadas(clave: string, porDefecto: number): number {
  try {
    const guardado = window.localStorage.getItem(`filas-por-pagina:${clave}`);
    const numero = guardado ? Number(guardado) : NaN;
    return OPCIONES.includes(numero) ? numero : porDefecto;
  } catch {
    return porDefecto;
  }
}

export function guardarFilasPorPagina(clave: string, valor: number): void {
  try {
    window.localStorage.setItem(`filas-por-pagina:${clave}`, String(valor));
  } catch {
    // almacenamiento no disponible (modo privado, bloqueado, etc.) — no pasa nada
  }
}
