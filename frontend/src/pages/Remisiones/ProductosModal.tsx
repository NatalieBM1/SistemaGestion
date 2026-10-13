import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { getApiErrorMessage } from "../../api/errors";
import {
  actualizarProductoRemision,
  crearProductoRemision,
  eliminarProductoRemision,
  getRemision,
  type RemisionProducto,
} from "../../api/remisiones";
import { Button, Modal, useToast } from "../../components/ui";
import { canWrite } from "../../lib/permissions";
import { formatMoney } from "../../lib/format";
import { useAuthStore } from "../../store/authStore";
import { PRODUCTO_DEFAULT, ProductoFormFields, type ProductoFormRow } from "./ProductoFormFields";
import styles from "../../components/CatalogoCRUD.module.css";
import tableStyles from "../../components/ui/Table.module.css";

type Vista = "lista" | "formulario";

/** Entrada rápida de productos desde el listado de remisiones (ícono "+" por
 * fila): un único Modal que alterna entre la tabla de productos ya
 * asociados y el formulario de línea (mismos campos y mutaciones que
 * ProductosSection, vía ProductoFormFields) — nunca abre un segundo Modal
 * encima, para evitar el anti-patrón de modal-dentro-de-modal. */
export function ProductosModal({
  remisionId,
  open,
  onClose,
}: {
  remisionId: number;
  open: boolean;
  onClose: () => void;
}) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);
  const puedeEscribir = canWrite(user);

  const [vista, setVista] = useState<Vista>("lista");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setVista("lista");
      setEditingId(null);
      setError(null);
    }
  }, [open]);

  const { data: remision } = useQuery({
    queryKey: ["remision", remisionId],
    queryFn: () => getRemision(remisionId),
    enabled: open,
  });

  const bloqueada = remision?.estado_facturacion === "FACTURADA";

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
      setVista("lista");
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
      setVista("lista");
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
    setVista("formulario");
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
    setVista("formulario");
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

  const productos = remision?.productos ?? [];
  const titulo =
    vista === "lista"
      ? `Productos de ${remision?.numero_remision ?? ""}`
      : editingId
        ? "Editar producto"
        : "Agregar producto";

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={titulo}
      size="lg"
      footer={
        vista === "formulario" ? (
          <>
            <Button type="button" variant="ghost" onClick={() => setVista("lista")}>
              Cancelar
            </Button>
            <Button
              type="submit"
              form="producto-modal-form"
              variant="primary"
              loading={crearMutation.isPending || actualizarMutation.isPending}
            >
              Guardar producto
            </Button>
          </>
        ) : undefined
      }
    >
      {vista === "lista" ? (
        <div>
          <div className={styles.toolbar} style={{ marginBottom: "var(--space-4)" }}>
            <span style={{ color: "var(--text-secondary)", fontSize: "var(--text-caption)" }}>
              {bloqueada
                ? "Esta remisión está totalmente facturada: los productos no se pueden modificar."
                : "Productos ya asociados a esta remisión."}
            </span>
            {!bloqueada && (
              <Button variant="primary" size="sm" leftIcon={<Plus size={16} />} onClick={openCreate} disabled={!puedeEscribir}>
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
                    <th>ID</th>
                    <th>Producto</th>
                    <th>Cantidad</th>
                    <th>Unidad</th>
                    <th>Valor material</th>
                    <th>Valor flete</th>
                    <th>Valor cama baja</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {productos.map((p) => (
                    <tr key={p.id}>
                      <td className="font-mono-data">{p.id}</td>
                      <td>{p.producto_nombre ?? p.producto_id}</td>
                      <td className="font-mono-data">{p.cantidad}</td>
                      <td>{p.unidad_medida_nombre ?? "—"}</td>
                      <td className="font-mono-data">{formatMoney(p.valor_material)}</td>
                      <td className="font-mono-data">{formatMoney(p.valor_flete)}</td>
                      <td className="font-mono-data">{formatMoney(p.valor_camabaja)}</td>
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
        </div>
      ) : (
        <form id="producto-modal-form" onSubmit={onSubmit} className={styles.form} noValidate>
          {error && <div className={styles.formError}>{error}</div>}
          <ProductoFormFields control={control} register={register} />
        </form>
      )}
    </Modal>
  );
}
