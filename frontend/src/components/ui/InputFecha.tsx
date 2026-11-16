import { Calendar, ChevronLeft, ChevronRight } from "lucide-react";
import {
  type KeyboardEvent as ReactKeyboardEvent,
  forwardRef,
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";
import inputStyles from "./Input.module.css";
import styles from "./InputFecha.module.css";

/** Campo de fecha: se puede ESCRIBIR (dd/mm/aaaa, las barras se ponen solas)
 * o ELEGIR en un calendario con listas de mes y año.
 *
 * El valor que recibe y entrega es ISO "AAAA-MM-DD" (o "" si está vacío o
 * incompleto), igual que un <input type="date">, así que el backend y los
 * filtros no cambian. */
export interface InputFechaProps {
  label?: string;
  value: string | null | undefined;
  onChange: (iso: string) => void;
  onBlur?: () => void;
  name?: string;
  error?: string;
  hint?: string;
  required?: boolean;
  readOnly?: boolean;
  disabled?: boolean;
  id?: string;
}

const MESES = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
];
const DIAS_CORTOS = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"];
const DIAS_LARGOS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"];
const ANIO_MIN = 1900;
const ANIO_MAX = 2100;

const dos = (n: number) => String(n).padStart(2, "0");
const aIso = (a: number, m: number, d: number) => `${a}-${dos(m + 1)}-${dos(d)}`;
const diasDelMes = (a: number, m: number) => new Date(a, m + 1, 0).getDate();
/** Lunes = 0 … domingo = 6 */
const diaSemana = (a: number, m: number, d: number) => (new Date(a, m, d).getDay() + 6) % 7;

function hoy(): { a: number; m: number; d: number } {
  const f = new Date();
  return { a: f.getFullYear(), m: f.getMonth(), d: f.getDate() };
}

function leerIso(iso: string | null | undefined): { a: number; m: number; d: number } | null {
  const r = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso ?? "");
  if (!r) return null;
  const a = Number(r[1]);
  const m = Number(r[2]) - 1;
  const d = Number(r[3]);
  return esValida(a, m, d) ? { a, m, d } : null;
}

function esValida(a: number, m: number, d: number): boolean {
  return a >= ANIO_MIN && a <= ANIO_MAX && m >= 0 && m <= 11 && d >= 1 && d <= diasDelMes(a, m);
}

const isoATexto = (iso: string | null | undefined) => {
  const f = leerIso(iso);
  return f ? `${dos(f.d)}/${dos(f.m + 1)}/${f.a}` : "";
};

/** "16/11/2026" (o con año de 2 dígitos "16/11/26") → ISO; null si no es válida. */
function textoAIso(texto: string): string | null {
  const r = /^(\d{1,2})\/(\d{1,2})\/(\d{2}|\d{4})$/.exec(texto.trim());
  if (!r) return null;
  const d = Number(r[1]);
  const m = Number(r[2]) - 1;
  const a = r[3].length === 2 ? 2000 + Number(r[3]) : Number(r[3]);
  return esValida(a, m, d) ? aIso(a, m, d) : null;
}

/** Arma "dd/mm/aaaa" mientras se escribe:
 *  - "16112026" → "16/11/2026" (las barras se ponen solas);
 *  - "1/2/26"  → "01/02/26" (si el usuario escribe la barra, completa con 0);
 *  - "2026-11-16" pegado → "16/11/2026". */
function enmascarar(texto: string, creciendo: boolean): string {
  const iso = /^(\d{4})-(\d{2})-(\d{2})$/.exec(texto.trim());
  if (iso) return `${iso[3]}/${iso[2]}/${iso[1]}`;
  const partes = ["", "", ""];
  let i = 0;
  for (const ch of texto) {
    if (/\d/.test(ch)) {
      if (i < 2 && partes[i].length === 2) i++;
      if (i === 2 && partes[2].length === 4) continue;
      partes[i] += ch;
    } else if ((ch === "/" || ch === "-" || ch === ".") && i < 2 && partes[i].length > 0) {
      partes[i] = partes[i].padStart(2, "0");
      i++;
    }
  }
  let out = partes[0];
  if (i >= 1) out += "/" + partes[1];
  if (i >= 2) out += "/" + partes[2];
  // Al escribir, la barra aparece apenas se completa el día o el mes.
  if (creciendo && i < 2 && partes[i].length === 2) out += "/";
  return out;
}

export const InputFecha = forwardRef<HTMLInputElement, InputFechaProps>(function InputFecha(
  { label, value, onChange, onBlur, name, error, hint, required, readOnly, disabled, id },
  ref,
) {
  const idGenerado = useId();
  const inputId = id ?? idGenerado;
  const [texto, setTexto] = useState(() => isoATexto(value));
  const [errorLocal, setErrorLocal] = useState<string | null>(null);
  const [abierto, setAbierto] = useState(false);
  const enfocado = useRef(false);
  const contenedor = useRef<HTMLDivElement>(null);
  const botonCal = useRef<HTMLButtonElement>(null);

  // Si el valor cambia desde afuera (Limpiar, reset del formulario, datos
  // cargados), se refleja en el texto, salvo mientras se está escribiendo
  // algo que todavía corresponde al mismo valor.
  useEffect(() => {
    if (enfocado.current && (textoAIso(texto) ?? "") === (value ?? "")) return;
    setTexto(isoATexto(value));
    if (value) setErrorLocal(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  const bloqueado = readOnly || disabled;

  const cambiarTexto = (nuevo: string) => {
    const t = enmascarar(nuevo, nuevo.length > texto.length);
    setTexto(t);
    setErrorLocal(null);
    const iso = textoAIso(t);
    if (iso) onChange(iso);
    else if (t === "" || (value ?? "") !== "") onChange("");
  };

  const alSalir = () => {
    enfocado.current = false;
    if (texto.trim() === "") setErrorLocal(null);
    else {
      const iso = textoAIso(texto);
      if (iso) {
        setTexto(isoATexto(iso)); // normaliza "1/2/26" → "01/02/2026"
        if (iso !== value) onChange(iso);
      } else setErrorLocal("Fecha no válida. Escríbela como dd/mm/aaaa.");
    }
    onBlur?.();
  };

  const elegir = (iso: string) => {
    setTexto(isoATexto(iso));
    setErrorLocal(null);
    onChange(iso);
    setAbierto(false);
    botonCal.current?.focus();
  };

  const mensajeError = errorLocal ?? error;

  return (
    <div
      className={inputStyles.field}
      ref={contenedor}
      onKeyDown={(e) => {
        // Esc con el foco en el campo o en el botón: cierra solo el calendario.
        if (e.key === "Escape" && abierto) {
          e.preventDefault();
          e.stopPropagation();
          setAbierto(false);
        }
      }}
    >
      {label && (
        <label className={inputStyles.label} htmlFor={inputId}>
          {label}
          {required && (
            <span className={inputStyles.required} aria-hidden="true">
              *
            </span>
          )}
        </label>
      )}
      <div className={inputStyles.inputWrapper}>
        <input
          ref={ref}
          id={inputId}
          name={name}
          type="text"
          inputMode="numeric"
          autoComplete="off"
          placeholder="dd/mm/aaaa"
          maxLength={10}
          required={required}
          readOnly={readOnly}
          disabled={disabled}
          value={texto}
          onFocus={() => (enfocado.current = true)}
          onChange={(e) => cambiarTexto(e.target.value)}
          onBlur={alSalir}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown" && e.altKey && !bloqueado) {
              e.preventDefault();
              setAbierto(true);
            }
          }}
          className={[inputStyles.input, inputStyles.hasRightElement, mensajeError ? inputStyles.inputError : "", "cifras"]
            .filter(Boolean)
            .join(" ")}
          aria-invalid={Boolean(mensajeError)}
          aria-describedby={mensajeError ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
        />
        <div className={inputStyles.rightElement}>
          <button
            ref={botonCal}
            type="button"
            className={styles.botonCalendario}
            onClick={() => setAbierto((a) => !a)}
            disabled={bloqueado}
            aria-label={label ? `Abrir calendario: ${label}` : "Abrir calendario"}
            title="Abrir calendario"
            aria-haspopup="dialog"
            aria-expanded={abierto}
          >
            <Calendar size={16} aria-hidden="true" />
          </button>
        </div>
      </div>
      {mensajeError ? (
        <span id={`${inputId}-error`} className={inputStyles.errorMessage} role="alert">
          {mensajeError}
        </span>
      ) : hint ? (
        <span id={`${inputId}-hint`} className={inputStyles.hint}>
          {hint}
        </span>
      ) : null}
      {abierto && (
        <Calendario
          ancla={contenedor}
          valor={textoAIso(texto) ?? value ?? ""}
          titulo={label}
          onElegir={elegir}
          onLimpiar={() => {
            setTexto("");
            setErrorLocal(null);
            onChange("");
            setAbierto(false);
            botonCal.current?.focus();
          }}
          onCerrar={() => {
            setAbierto(false);
            botonCal.current?.focus();
          }}
        />
      )}
    </div>
  );
});

interface CalendarioProps {
  ancla: React.RefObject<HTMLDivElement | null>;
  valor: string;
  titulo?: string;
  onElegir: (iso: string) => void;
  onLimpiar: () => void;
  onCerrar: () => void;
}

function Calendario({ ancla, valor, titulo, onElegir, onLimpiar, onCerrar }: CalendarioProps) {
  const seleccion = leerIso(valor);
  const h = hoy();
  const inicio = seleccion ?? h;
  const [vista, setVista] = useState({ a: inicio.a, m: inicio.m });
  const [foco, setFoco] = useState(inicio.d);
  const panel = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState<{ top: number; left: number } | null>(null);

  // Posición fija junto al campo (fuera de los modales, que recortan).
  const ubicar = useCallback(() => {
    const cont = ancla.current?.querySelector("input")?.getBoundingClientRect();
    const p = panel.current;
    if (!cont || !p) return;
    const ancho = p.offsetWidth;
    const alto = p.offsetHeight;
    const margen = 8;
    let top = cont.bottom + 6;
    if (top + alto > window.innerHeight - margen) {
      // No cabe abajo: arriba del campo si hay espacio; si no, pegado al borde
      // inferior de la ventana (puede tapar el campo, pero no se corta).
      top = cont.top - alto - 6 > margen ? cont.top - alto - 6 : window.innerHeight - alto - margen;
    }
    const left = Math.min(Math.max(margen, cont.left), window.innerWidth - ancho - margen);
    setPos({ top: Math.max(margen, top), left });
  }, [ancla]);

  useLayoutEffect(() => {
    ubicar();
  }, [ubicar, vista]);

  useEffect(() => {
    const fuera = (e: MouseEvent) => {
      const t = e.target as Node;
      if (!panel.current?.contains(t) && !ancla.current?.contains(t)) onCerrar();
    };
    window.addEventListener("resize", ubicar);
    window.addEventListener("scroll", ubicar, true);
    document.addEventListener("mousedown", fuera);
    return () => {
      window.removeEventListener("resize", ubicar);
      window.removeEventListener("scroll", ubicar, true);
      document.removeEventListener("mousedown", fuera);
    };
  }, [ancla, onCerrar, ubicar]);

  // Foco en el día al abrir y al moverse con el teclado. Espera a que el
  // panel tenga posición: mientras está oculto no puede recibir el foco.
  const ubicado = pos !== null;
  useEffect(() => {
    if (!ubicado) return;
    panel.current?.querySelector<HTMLButtonElement>(`[data-dia="${foco}"]`)?.focus();
  }, [foco, vista, ubicado]);

  const total = diasDelMes(vista.a, vista.m);
  const vacios = diaSemana(vista.a, vista.m, 1);

  const irA = (a: number, m: number, d: number) => {
    const fecha = new Date(a, m, d);
    const na = Math.min(ANIO_MAX, Math.max(ANIO_MIN, fecha.getFullYear()));
    setVista({ a: na, m: fecha.getMonth() });
    setFoco(Math.min(fecha.getDate(), diasDelMes(na, fecha.getMonth())));
  };
  const cambiarMes = (delta: number) => {
    const n = new Date(vista.a, vista.m + delta, 1);
    if (n.getFullYear() < ANIO_MIN || n.getFullYear() > ANIO_MAX) return;
    setVista({ a: n.getFullYear(), m: n.getMonth() });
    setFoco((f) => Math.min(f, diasDelMes(n.getFullYear(), n.getMonth())));
  };

  const teclas = (e: ReactKeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation(); // no cerrar el modal que contiene el campo
      onCerrar();
      return;
    }
    const enDia = (e.target as HTMLElement).dataset.dia !== undefined;
    if (!enDia) return;
    const mover: Record<string, number> = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
    if (e.key in mover) {
      e.preventDefault();
      irA(vista.a, vista.m, foco + mover[e.key]);
    } else if (e.key === "PageUp" || e.key === "PageDown") {
      e.preventDefault();
      const delta = e.key === "PageUp" ? -1 : 1;
      if (e.shiftKey) irA(vista.a + delta, vista.m, foco);
      else irA(vista.a, vista.m + delta, Math.min(foco, diasDelMes(vista.a, vista.m + delta)));
    } else if (e.key === "Home") {
      e.preventDefault();
      setFoco(1);
    } else if (e.key === "End") {
      e.preventDefault();
      setFoco(total);
    }
  };

  const anios: number[] = [];
  const desde = Math.min(h.a - 30, vista.a);
  const hasta = Math.max(h.a + 10, vista.a);
  for (let a = hasta; a >= desde; a--) anios.push(a);

  const celdas: (number | null)[] = [...Array(vacios).fill(null), ...Array.from({ length: total }, (_, i) => i + 1)];
  while (celdas.length % 7) celdas.push(null);
  const semanas: (number | null)[][] = [];
  for (let i = 0; i < celdas.length; i += 7) semanas.push(celdas.slice(i, i + 7));

  return createPortal(
    <div
      ref={panel}
      className={styles.panel}
      role="dialog"
      aria-modal="false"
      aria-label={titulo ? `Elegir fecha: ${titulo}` : "Elegir fecha"}
      style={pos ? { top: pos.top, left: pos.left } : { visibility: "hidden", top: 0, left: 0 }}
      onKeyDown={teclas}
    >
      <div className={styles.cabecera}>
        <button type="button" className={styles.flecha} onClick={() => cambiarMes(-1)} aria-label="Mes anterior">
          <ChevronLeft size={16} aria-hidden="true" />
        </button>
        <select
          className={styles.selector}
          value={vista.m}
          onChange={(e) => {
            const m = Number(e.target.value);
            setVista((v) => ({ ...v, m }));
            setFoco((f) => Math.min(f, diasDelMes(vista.a, m)));
          }}
          aria-label="Mes"
        >
          {MESES.map((nombre, i) => (
            <option key={nombre} value={i}>
              {nombre[0].toUpperCase() + nombre.slice(1)}
            </option>
          ))}
        </select>
        <select
          className={`${styles.selector} ${styles.selectorAnio}`}
          value={vista.a}
          onChange={(e) => {
            const a = Number(e.target.value);
            setVista((v) => ({ ...v, a }));
            setFoco((f) => Math.min(f, diasDelMes(a, vista.m)));
          }}
          aria-label="Año"
        >
          {anios.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
        <button type="button" className={styles.flecha} onClick={() => cambiarMes(1)} aria-label="Mes siguiente">
          <ChevronRight size={16} aria-hidden="true" />
        </button>
      </div>

      <table className={styles.mes} role="grid" aria-label={`${MESES[vista.m]} de ${vista.a}`}>
        <thead>
          <tr>
            {DIAS_CORTOS.map((d, i) => (
              <th key={d} scope="col" abbr={DIAS_LARGOS[i]}>
                {d}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {semanas.map((semana, i) => (
            <tr key={i}>
              {semana.map((d, j) =>
                d === null ? (
                  <td key={j} />
                ) : (
                  <td key={j}>
                    <button
                      type="button"
                      data-dia={d}
                      tabIndex={d === foco ? 0 : -1}
                      className={[
                        styles.dia,
                        seleccion && seleccion.a === vista.a && seleccion.m === vista.m && seleccion.d === d ? styles.diaElegido : "",
                        h.a === vista.a && h.m === vista.m && h.d === d ? styles.diaHoy : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                      aria-pressed={Boolean(seleccion && seleccion.a === vista.a && seleccion.m === vista.m && seleccion.d === d)}
                      aria-label={`${DIAS_LARGOS[diaSemana(vista.a, vista.m, d)]}, ${d} de ${MESES[vista.m]} de ${vista.a}`}
                      onClick={() => onElegir(aIso(vista.a, vista.m, d))}
                    >
                      {d}
                    </button>
                  </td>
                ),
              )}
            </tr>
          ))}
        </tbody>
      </table>

      <div className={styles.pie}>
        <button type="button" className={styles.accion} onClick={onLimpiar}>
          Limpiar
        </button>
        <button type="button" className={styles.accion} onClick={() => onElegir(aIso(h.a, h.m, h.d))}>
          Hoy
        </button>
      </div>
    </div>,
    document.body,
  );
}
