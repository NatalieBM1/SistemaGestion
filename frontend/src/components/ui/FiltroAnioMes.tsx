import { Select } from "./Select";

/** Primer año con datos en el sistema (histórico desde septiembre de 2023). */
export const ANIO_INICIAL = 2023;

export const MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

/** Años disponibles, del más reciente al más antiguo. */
export function aniosDisponibles(): number[] {
  const actual = new Date().getFullYear();
  const anios: number[] = [];
  for (let a = Math.max(actual, ANIO_INICIAL); a >= ANIO_INICIAL; a--) anios.push(a);
  return anios;
}

interface Props {
  anio: number | null;
  mes: number | null;
  onChange: (anio: number | null, mes: number | null) => void;
  /** Texto que aclara qué fecha se usa (ej. "de la remisión"). */
  sufijo?: string;
}

/** Dos listas (Año y Mes) para filtrar listados. "Todos" = sin filtro. */
export function FiltroAnioMes({ anio, mes, onChange, sufijo = "" }: Props) {
  return (
    <>
      <Select
        label={`Año${sufijo}`}
        value={anio ?? ""}
        onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null, mes)}
      >
        <option value="">Todos</option>
        {aniosDisponibles().map((a) => (
          <option key={a} value={a}>
            {a}
          </option>
        ))}
      </Select>
      <Select
        label={`Mes${sufijo}`}
        value={mes ?? ""}
        onChange={(e) => onChange(anio, e.target.value ? Number(e.target.value) : null)}
      >
        <option value="">Todos</option>
        {MESES.map((nombre, i) => (
          <option key={nombre} value={i + 1}>
            {nombre}
          </option>
        ))}
      </Select>
    </>
  );
}
