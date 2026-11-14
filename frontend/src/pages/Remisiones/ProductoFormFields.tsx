import type { Control, UseFormRegister } from "react-hook-form";
import { Controller } from "react-hook-form";
import { AsyncSelect, InputNumero } from "../../components/ui";
import { formatUnidad } from "../../lib/format";

export interface ProductoFormRow {
  producto_id: number | null;
  cantidad: string;
  unidad_medida_id: number | null;
  valor_material: string;
  valor_flete: string;
  valor_camabaja: string;
  numero_viajes: string;
  valor_comision: string;
  valor_costo: string;
}

export const PRODUCTO_DEFAULT: ProductoFormRow = {
  producto_id: null,
  cantidad: "1",
  unidad_medida_id: null,
  valor_material: "0",
  valor_flete: "0",
  valor_camabaja: "0",
  numero_viajes: "1",
  valor_comision: "0",
  valor_costo: "0",
};

type CampoNumerico = Exclude<keyof ProductoFormRow, "producto_id" | "unidad_medida_id">;

function CampoNumero({
  control,
  name,
  label,
  moneda,
  entero,
}: {
  control: Control<ProductoFormRow>;
  name: CampoNumerico;
  label: string;
  moneda?: boolean;
  entero?: boolean;
}) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field }) => (
        <InputNumero
          label={label}
          moneda={moneda}
          entero={entero}
          value={field.value ?? ""}
          onChange={field.onChange}
          onBlur={field.onBlur}
          name={field.name}
        />
      )}
    />
  );
}

/** Los 9 campos del formulario de línea de producto, compartidos entre
 * ProductosSection (formulario completo de la remisión) y ProductosModal
 * (entrada rápida desde el listado) para no duplicar este markup. */
export function ProductoFormFields({
  control,
  conCamabaja,
}: {
  control: Control<ProductoFormRow>;
  /** Se mantiene por compatibilidad con quien lo pasa; los campos numéricos
   * van con Controller (InputNumero). */
  register?: UseFormRegister<ProductoFormRow>;
  /** El valor de cama baja solo existe si la remisión tiene cama baja. */
  conCamabaja: boolean;
}) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "var(--space-3)" }}>
      <Controller
        control={control}
        name="producto_id"
        render={({ field }) => (
          <AsyncSelect
            label="Producto"
            endpoint="/api/catalogos/productos"
            getLabel={(item) => String(item.nombre)}
            value={field.value}
            onChange={field.onChange}
            required
          />
        )}
      />
      <Controller
        control={control}
        name="unidad_medida_id"
        render={({ field }) => (
          <AsyncSelect
            label="Unidad de medida"
            endpoint="/api/catalogos/unidades_medida"
            getLabel={(item) => formatUnidad(String(item.nombre))}
            value={field.value}
            onChange={field.onChange}
          />
        )}
      />
      <CampoNumero control={control} name="cantidad" label="Cantidad" />
      <CampoNumero control={control} name="valor_material" label="Valor material" moneda />
      <CampoNumero control={control} name="valor_flete" label="Valor flete" moneda />
      {conCamabaja && <CampoNumero control={control} name="valor_camabaja" label="Valor cama baja" moneda />}
      <CampoNumero control={control} name="numero_viajes" label="Número de viajes" entero />
      <CampoNumero control={control} name="valor_comision" label="Valor comisión" moneda />
      <CampoNumero control={control} name="valor_costo" label="Valor costo" moneda />
    </div>
  );
}
