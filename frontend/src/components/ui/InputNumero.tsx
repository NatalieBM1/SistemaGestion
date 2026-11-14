import { useState, type ComponentProps } from "react";
import { formatCantidad, formatCOP, parseNumeroEsCO } from "../../lib/format";
import { Input } from "./Input";

type InputProps = Omit<ComponentProps<typeof Input>, "value" | "onChange" | "type">;

interface InputNumeroProps extends InputProps {
  /** Valor como lo maneja el formulario/la API: "1234.5" ("" = vacío). */
  value: string;
  onChange: (valor: string) => void;
  /** Pesos: al salir del campo se muestra "1.234.567,50". */
  moneda?: boolean;
  /** Solo enteros (p. ej. número de viajes). */
  entero?: boolean;
}

/** Texto para editar: sin separador de miles y con coma decimal. */
function paraEditar(valor: string): string {
  if (valor === "") return "";
  const n = Number(valor);
  return Number.isFinite(n) ? String(n).replace(".", ",") : valor;
}

/** Campo numérico en formato es-CO: acepta coma decimal (y puntos de
 * miles) al escribir, muestra el separador de miles al salir del campo, y
 * entrega al formulario el número normalizado ("1234.5"). No cambia lo que
 * se guarda en la base: solo cómo se escribe y se ve. */
export function InputNumero({ value, onChange, moneda, entero, onBlur, onFocus, ...rest }: InputNumeroProps) {
  const [editando, setEditando] = useState(false);
  const [texto, setTexto] = useState("");

  const mostrado = editando
    ? texto
    : value === ""
      ? ""
      : moneda
        ? formatCOP(value).replace("$ ", "")
        : formatCantidad(value);

  return (
    <Input
      {...rest}
      type="text"
      inputMode={entero ? "numeric" : "decimal"}
      leftElement={moneda && !rest.leftElement ? <span aria-hidden="true">$</span> : rest.leftElement}
      value={mostrado}
      onFocus={(event) => {
        setTexto(paraEditar(value));
        setEditando(true);
        onFocus?.(event);
      }}
      onChange={(event) => {
        const escrito = event.target.value;
        if (entero && /[.,]/.test(escrito)) return;
        setTexto(escrito);
        const normalizado = parseNumeroEsCO(escrito);
        if (normalizado !== null) onChange(normalizado);
      }}
      onBlur={(event) => {
        setEditando(false);
        onBlur?.(event);
      }}
    />
  );
}
