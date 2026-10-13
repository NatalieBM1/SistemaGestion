import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { apiClient } from "../../api/client";
import { getEmpresa } from "../../api/empresa";
import { getRemision } from "../../api/remisiones";
import { getTercero } from "../../api/terceros";
import { Button } from "../../components/ui";
import { ReciboRemision } from "./ReciboRemision";
import styles from "./ImprimirRemision.module.css";

interface NombreItem {
  nombre: string;
}

/** Vista imprimible de una remisión, en su propia ruta fuera de MainLayout
 * (sin sidebar/header) para que el CSS del resto de la app no interfiera
 * con @media print. Reproduce el formato físico real (REMISION.xlsm, hoja
 * "Imprimir"): 3 copias por hoja carta para cortar después de imprimir.
 * Dispara window.print() automáticamente una vez que todos los datos
 * (incluidos los nombres resueltos de catálogos) terminaron de cargar. */
export function ImprimirRemision() {
  const params = useParams<{ id: string }>();
  const remisionId = Number(params.id);

  const { data: remision, isLoading: cargandoRemision } = useQuery({
    queryKey: ["remision-imprimir", remisionId],
    queryFn: () => getRemision(remisionId),
    enabled: Number.isFinite(remisionId),
  });

  const { data: empresa } = useQuery({ queryKey: ["empresa"], queryFn: getEmpresa });

  const { data: cliente } = useQuery({
    queryKey: ["tercero-imprimir", remision?.cliente_id],
    queryFn: () => getTercero(remision!.cliente_id),
    enabled: remision != null,
  });

  const { data: conductor } = useQuery({
    queryKey: ["tercero-imprimir", remision?.conductor_id],
    queryFn: () => getTercero(remision!.conductor_id as number),
    enabled: remision?.conductor_id != null,
  });

  const { data: formaPago } = useQuery({
    queryKey: ["forma-pago-imprimir", remision?.forma_pago_id],
    queryFn: async () => {
      const { data } = await apiClient.get<NombreItem>(`/api/catalogos/formas_pago/${remision!.forma_pago_id}`);
      return data;
    },
    enabled: remision?.forma_pago_id != null,
  });

  const { data: proyecto } = useQuery({
    queryKey: ["proyecto-imprimir", remision?.proyecto_id],
    queryFn: async () => {
      const { data } = await apiClient.get<NombreItem>(`/api/catalogos/proyectos/${remision!.proyecto_id}`);
      return data;
    },
    enabled: remision?.proyecto_id != null,
  });

  const { data: tramo } = useQuery({
    queryKey: ["tramo-imprimir", remision?.tramo_id],
    queryFn: async () => {
      const { data } = await apiClient.get<NombreItem>(`/api/catalogos/tramos/${remision!.tramo_id}`);
      return data;
    },
    enabled: remision?.tramo_id != null,
  });

  const { data: tipoServicio } = useQuery({
    queryKey: ["tipo-servicio-imprimir", remision?.tipo_servicio_id],
    queryFn: async () => {
      const { data } = await apiClient.get<NombreItem>(`/api/catalogos/tipos_servicio/${remision!.tipo_servicio_id}`);
      return data;
    },
    enabled: remision?.tipo_servicio_id != null,
  });

  const { data: ordenServicio } = useQuery({
    queryKey: ["orden-servicio-imprimir", remision?.orden_servicio_id],
    queryFn: async () => {
      const { data } = await apiClient.get<{ numero: string }>(`/api/ordenes-servicio/${remision!.orden_servicio_id}`);
      return data;
    },
    enabled: remision?.orden_servicio_id != null,
  });

  const tramoNombre = tramo?.nombre ?? null;

  const listoParaImprimir =
    remision != null &&
    empresa != null &&
    cliente != null &&
    (remision.conductor_id == null || conductor != null) &&
    (remision.forma_pago_id == null || formaPago != null) &&
    (remision.proyecto_id == null || proyecto != null) &&
    (remision.tramo_id == null || tramo != null) &&
    (remision.tipo_servicio_id == null || tipoServicio != null) &&
    (remision.orden_servicio_id == null || ordenServicio != null);

  useEffect(() => {
    if (!listoParaImprimir || !remision) return;
    document.title = `Remisión ${remision.numero_remision}`;
    const timeout = setTimeout(() => window.print(), 400);
    return () => clearTimeout(timeout);
  }, [listoParaImprimir, remision]);

  if (cargandoRemision || !listoParaImprimir || !remision || !empresa) {
    return <div className={styles.page}>Cargando remisión…</div>;
  }

  const reciboProps = {
    remision,
    empresa,
    clienteIdentificacion: cliente?.identificacion ?? null,
    conductorIdentificacion: conductor?.identificacion ?? null,
    formaPagoNombre: formaPago?.nombre ?? null,
    proyectoNombre: proyecto?.nombre ?? null,
    tramoNombre,
    tipoServicioNombre: tipoServicio?.nombre ?? null,
    ordenServicioNumero: ordenServicio?.numero ?? null,
  };

  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <Button variant="ghost" onClick={() => window.close()}>
          Cerrar pestaña
        </Button>
        <Button variant="primary" onClick={() => window.print()}>
          Imprimir
        </Button>
      </div>

      <div className={styles.hoja}>
        <div className={styles.filaSuperior}>
          <ReciboRemision {...reciboProps} />
          <ReciboRemision {...reciboProps} />
        </div>
        <div className={styles.filaInferior}>
          <ReciboRemision {...reciboProps} />
        </div>
      </div>
    </div>
  );
}
