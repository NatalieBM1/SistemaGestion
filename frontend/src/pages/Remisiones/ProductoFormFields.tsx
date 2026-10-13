import type { Control, UseFormRegister } from "react-hook-form";
import { Controller } from "react-hook-form";
import { AsyncSelect, Input } from "../../components/ui";

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

/** Los 9 campos del formulario de línea de producto, compartidos entre
 * ProductosSection (formulario completo de la remisión) y ProductosModal
 * (entrada rápida desde el listado) para no duplicar este markup. */
export function ProductoFormFields({
  control,
  register,
}: {
  control: Control<ProductoFormRow>;
  register: UseFormRegister<ProductoFormRow>;
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
            getLabel={(item) => String(item.nombre)}
            value={field.value}
            onChange={field.onChange}
          />
        )}
      />
      <Input label="Cantidad" type="number" step="0.001" {...register("cantidad")} />
      <Input label="Valor material" type="number" step="0.01" {...register("valor_material")} />
      <Input label="Valor flete" type="number" step="0.01" {...register("valor_flete")} />
      <Input label="Valor cama baja" type="number" step="0.01" {...register("valor_camabaja")} />
      <Input label="Número de viajes" type="number" {...register("numero_viajes")} />
      <Input label="Valor comisión" type="number" step="0.01" {...register("valor_comision")} />
      <Input label="Valor costo" type="number" step="0.01" {...register("valor_costo")} />
    </div>
  );
}
