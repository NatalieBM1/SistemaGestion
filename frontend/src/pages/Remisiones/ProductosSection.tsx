import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { getApiErrorMessage } from "../../api/errors";
import {
  actualizarProductoRemision,
  crearProductoRemision,
  eliminarProductoRemision,
  type RemisionProducto,
} from "../../api/remisiones";
import { Button, Modal, useToast } from "../../components/ui";
import { PRODUCTO_DEFAULT, ProductoFormFields, type ProductoFormRow } from "./ProductoFormFields";
import styles from "../../components/CatalogoCRUD.module.css";
import tableStyles from "../../components/ui/Table.module.css";

/** Sección de productos dentro del formulario completo de una remisión:
 * tabla inline + botón que abre un Modal con el formulario de línea. Se usa
 * embebida en la página (no dentro de otro Modal), así que el Modal interno
 * no genera anidamiento. Para la entrada rápida desde el listado, ver
 * ProductosModal.tsx, que reutiliza ProductoFormFields pero sin anidar
 * modales. */
export function ProductosSection({
  remisionId,
  productos,
  bloqueada,
  puedeEscribir,
}: {
  remisionId: number;
  productos: RemisionProducto[];
  bloqueada: boolean;
  puedeEscribir: boolean;
}) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { control, register, handleSubmit, reset } = useForm<ProductoFormRow>({
    defaultValues: PRODUCTO_DEFAULT,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["remision", remisionId] });
    queryClient.invalidateQueries({ queryKey: ["remisiones"] });
  };

  const crearMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => crearProductoRemision(remisionId, payload),
    onSuccess: ({ alerta_saldo_bajo }) => {
      invalidate();
      setFormOpen(false);
      reset(PRODUCTO_DEFAULT);
      toast.success("Producto agregado correctamente.");
      if (alerta_saldo_bajo) toast.error(alerta_saldo_bajo);
    },
    onError: (err) => setError(getApiErrorMessage(err, "No se pudo agregar el producto.")),
  });

  const actualizarMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Record<string, unknown> }) =>
      actualizarProductoRemision(remisionId, id, payload),
    onSuccess: ({ alerta_saldo_bajo }) => {
      invalidate();
      setFormOpen(false);
      setEditingId(null);
      reset(PRODUCTO_DEFAULT);
      toast.success("Producto actualizado correctamente.");
      if (alerta_saldo_bajo) toast.error(alerta_saldo_bajo);
    },
    onError: (err) => setError(getApiErrorMessage(err, "No se pudo actualizar el producto.")),
  });

  const eliminarMutation = useMutation({
    mutationFn: (id: number) => eliminarProductoRemision(remisionId, id),
    onSuccess: () => {
      invalidate();
      toast.success("Producto eliminado correctamente.");
    },
    onError: (err) => toast.error(getApiErrorMessage(err, "No se pudo eliminar el producto.")),
  });

  const openCreate = () => {
    setEditingId(null);
    setError(null);
    reset(PRODUCTO_DEFAULT);
    setFormOpen(true);
  };

  const openEdit = (p: RemisionProducto) => {
    setEditingId(p.id);
    setError(null);
    reset({
      producto_id: p.producto_id,
      cantidad: p.cantidad,
      unidad_medida_id: p.unidad_medida_id,
      valor_material: p.valor_material,
      valor_flete: p.valor_flete,
      valor_camabaja: p.valor_camabaja,
      numero_viajes: String(p.numero_viajes),
      valor_comision: p.valor_comision,
      valor_costo: p.valor_costo,
    });
    setFormOpen(true);
  };

  const onSubmit = handleSubmit((values) => {
    setError(null);
    if (!values.producto_id) {
      setError("Selecciona un producto.");
      return;
    }
    const payload = {
      producto_id: values.producto_id,
      cantidad: Number(values.cantidad),
      unidad_medida_id: values.unidad_medida_id,
      valor_material: Number(values.valor_material),
      valor_flete: Number(values.valor_flete),
      valor_camabaja: Number(values.valor_camabaja),
      numero_viajes: Number(values.numero_viajes),
      valor_comision: Number(values.valor_comision),
      valor_costo: Number(values.valor_costo),
    };
    if (editingId) {
      actualizarMutation.mutate({ id: editingId, payload });
    } else {
      crearMutation.mutate(payload);
    }
  });

  return (
    <div style={{ marginTop: "var(--space-6)" }}>
      <div className={styles.toolbar}>
        <h3 style={{ margin: 0 }}>Productos</h3>
        {!bloqueada && (
          <Button variant="primary" leftIcon={<Plus size={16} />} onClick={openCreate} disabled={!puedeEscribir}>
            Agregar producto
          </Button>
        )}
      </div>

      {productos.length === 0 ? (
        <p style={{ color: "var(--text-secondary)" }}>Sin productos asociados todavía.</p>
      ) : (
        <div className={tableStyles.wrapper}>
          <table className={tableStyles.table}>
            <thead>
              <tr>
                <th>Producto</th>
                <th>Cantidad</th>
                <th>Material</th>
                <th>Flete</th>
                <th>Viajes</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {productos.map((p) => (
                <tr key={p.id}>
                  <td>{p.producto_nombre ?? p.producto_id}</td>
                  <td className="font-mono-data">
                    {p.cantidad} {p.unidad_medida_nombre ?? ""}
                  </td>
                  <td className="font-mono-data">{p.valor_material}</td>
                  <td className="font-mono-data">{p.valor_flete}</td>
                  <td className="font-mono-data">{p.numero_viajes}</td>
                  <td className={tableStyles.alignRight}>
                    {!bloqueada && (
                      <div className={tableStyles.actionsCell}>
                        <button
                          type="button"
                          onClick={() => openEdit(p)}
                          disabled={!puedeEscribir}
                          className={tableStyles.actionButton}
                          aria-label="Editar producto"
                        >
                          Editar
                        </button>
                        <button
                          type="button"
                          onClick={() => eliminarMutation.mutate(p.id)}
                          disabled={!puedeEscribir}
                          className={[tableStyles.actionButton, tableStyles.danger].join(" ")}
                          aria-label="Eliminar producto"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        open={formOpen}
        onClose={() => setFormOpen(false)}
        title={editingId ? "Editar producto" : "Agregar producto"}
        size="lg"
        footer={
          <>
            <Button type="button" variant="ghost" onClick={() => setFormOpen(false)}>
              Cancelar
            </Button>
            <Button
              type="submit"
              form="producto-form"
              variant="primary"
              loading={crearMutation.isPending || actualizarMutation.isPending}
            >
              Guardar producto
            </Button>
          </>
        }
      >
        <form id="producto-form" onSubmit={onSubmit} className={styles.form} noValidate>
          {error && <div className={styles.formError}>{error}</div>}
          <ProductoFormFields control={control} register={register} />
        </form>
      </Modal>
    </div>
  );
}
