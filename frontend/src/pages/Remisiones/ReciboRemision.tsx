import type { Empresa } from "../../api/empresa";
import type { RemisionDetalle } from "../../api/remisiones";
import logo from "../../assets/Logo_Transportes.png";
import styles from "./ReciboRemision.module.css";

export interface ReciboRemisionProps {
  remision: RemisionDetalle;
  empresa: Empresa;
  clienteIdentificacion: string | null;
  conductorIdentificacion: string | null;
  formaPagoNombre: string | null;
  proyectoNombre: string | null;
  tramoNombre: string | null;
  tipoServicioNombre: string | null;
  ordenServicioNumero: string | null;
}

/** Fila de dos campos lado a lado (etiqueta + valor subrayado, dos veces),
 * como en la hoja "Imprimir": p. ej. "Forma de pago ... Orden Servicio ...". */
function FilaDoble({
  label1,
  value1,
  label2,
  value2,
  align1 = "left",
  align2 = "left",
  label2Small = false,
}: {
  label1: string;
  value1: string;
  label2: string;
  value2: string;
  align1?: "left" | "center";
  align2?: "left" | "center";
  label2Small?: boolean;
}) {
  return (
    <div className={styles.filaDoble}>
      <span className={styles.label}>{label1}</span>
      <span className={[styles.valor, align1 === "center" ? styles.valorCentro : ""].join(" ")}>{value1}</span>
      <span className={[styles.label, label2Small ? styles.labelPequena : ""].join(" ")}>{label2}</span>
      <span className={[styles.valor, align2 === "center" ? styles.valorCentro : ""].join(" ")}>{value2}</span>
    </div>
  );
}

/** Fila de un solo campo a todo el ancho: etiqueta + valor subrayado. */
function FilaSimple({ label, value, alto }: { label: string; value: string; alto?: boolean }) {
  return (
    <div className={[styles.filaSimple, alto ? styles.filaAlta : ""].join(" ")}>
      <span className={styles.label}>{label}</span>
      <span className={styles.valor}>{value}</span>
    </div>
  );
}

/** Fila con identificación (angosta) + nombre (ancha), con una sola línea
 * continua debajo de ambas — así aparecen Cliente y Conductor en la hoja. */
function FilaIdentificado({ label, identificacion, nombre }: { label: string; identificacion: string; nombre: string }) {
  return (
    <div className={styles.filaIdentificado}>
      <span className={styles.label}>{label}</span>
      <span className={styles.valorAngosto}>{identificacion}</span>
      <span className={styles.valorAncho}>{nombre}</span>
    </div>
  );
}

/** Una copia del recibo de remisión, en el orden exacto del formato físico
 * (RemisionesTG&G.xlsm, hoja "Imprimir") que firman cliente y conductor. Se
 * renderiza 3 veces por hoja desde ImprimirRemision.tsx — este componente
 * no sabe nada del triplicado, solo dibuja una copia. */
export function ReciboRemision({
  remision,
  empresa,
  clienteIdentificacion,
  conductorIdentificacion,
  formaPagoNombre,
  proyectoNombre,
  tramoNombre,
  tipoServicioNombre,
  ordenServicioNumero,
}: ReciboRemisionProps) {
  const productos = remision.productos;
  const obraYTramo = [proyectoNombre, tramoNombre].filter(Boolean).join(" — ") || "";
  // "0" quedó así en el registro histórico de la empresa (dato faltante en
  // el Excel original, no un teléfono real) — no se imprime como si lo fuera.
  const telefonoEmpresa = empresa.telefono && empresa.telefono !== "0" ? empresa.telefono : null;
  const unProducto = productos.length <= 1;

  return (
    <div className={styles.recibo}>
      <div className={styles.header}>
        <img src={logo} alt={empresa.nombre} className={styles.logo} />
        <div className={styles.empresaInfo}>
          <p className={styles.empresaLinea}>{empresa.nombre}</p>
          <p className={styles.empresaLinea}>{empresa.nit}</p>
          {empresa.direccion && <p className={styles.empresaLinea}>{empresa.direccion}</p>}
          {empresa.ciudad && <p className={styles.empresaLinea}>{empresa.ciudad}</p>}
          {empresa.email && <p className={styles.empresaLinea}>{empresa.email}</p>}
          {empresa.responsabilidad_iva && <p className={styles.empresaLinea}>{empresa.responsabilidad_iva}</p>}
          {telefonoEmpresa && <p className={styles.empresaLinea}>{telefonoEmpresa}</p>}
          <p className={styles.empresaLinea}>{empresa.resolucion_habilitacion}</p>
        </div>
      </div>

      <div className={styles.filaRemision}>
        <span className={styles.label}>Remision</span>
        <span className={styles.numero}>{remision.numero_remision}</span>
        <span className={styles.label}>Fecha</span>
        <span className={styles.valor}>{remision.fecha}</span>
      </div>

      <FilaDoble
        label1="Forma de pago"
        value1={formaPagoNombre ?? ""}
        label2="Orden Servicio"
        value2={ordenServicioNumero ?? ""}
        label2Small
      />

      <FilaIdentificado label="Cliente" identificacion={clienteIdentificacion ?? ""} nombre={remision.cliente_nombre ?? ""} />

      <FilaSimple label="Obra y tramo" value={obraYTramo} />
      <FilaSimple label="Origen" value={remision.origen_municipio_nombre ?? ""} />
      <FilaSimple label="Destino" value={remision.destino_municipio_nombre ?? ""} />

      <FilaDoble
        label1="Kilometros"
        value1={remision.kilometros ?? ""}
        label2="Vehiculo"
        value2={remision.vehiculo_placa ?? ""}
        align1="center"
        align2="center"
      />

      <FilaDoble
        label1="Hora salida"
        value1={remision.hora_salida ?? ""}
        label2="Hora llegada"
        value2={remision.hora_llegada ?? ""}
        align1="center"
        align2="center"
      />

      <FilaIdentificado label="Conductor" identificacion={conductorIdentificacion ?? ""} nombre={remision.conductor_nombre ?? ""} />

      {unProducto ? (
        <>
          <FilaDoble
            label1="Servicio"
            value1={tipoServicioNombre ?? ""}
            label2="Producto"
            value2={productos[0]?.producto_nombre ?? ""}
          />
          <FilaDoble
            label1="Cantidad"
            value1={productos[0]?.cantidad ?? ""}
            label2="Unidad Medida"
            value2={productos[0]?.unidad_medida_nombre ?? ""}
            align1="center"
          />
        </>
      ) : (
        <table className={styles.miniTable}>
          <thead>
            <tr>
              <th>Servicio</th>
              <th>Producto</th>
              <th>Cantidad</th>
              <th>Unidad Medida</th>
            </tr>
          </thead>
          <tbody>
            {productos.map((p) => (
              <tr key={p.id}>
                <td>{tipoServicioNombre ?? ""}</td>
                <td>{p.producto_nombre ?? ""}</td>
                <td>{p.cantidad}</td>
                <td>{p.unidad_medida_nombre ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <FilaSimple label="Observación:" value={remision.observaciones ?? ""} alto />

      <div className={styles.firmas}>
        <div className={styles.firma}>
          <div className={styles.firmaLinea} />
          <div className={styles.firmaCaption}>Vendedor</div>
          <div className={styles.firmaCampo}>
            <span className={styles.label}>CC No</span>
            <span className={styles.valor} />
          </div>
        </div>
        <div className={styles.firma}>
          <div className={styles.firmaLinea} />
          <div className={styles.firmaCaption}>Recibe</div>
          <div className={styles.firmaCampo}>
            <span className={styles.label}>CC No</span>
            <span className={styles.valor} />
          </div>
          <div className={styles.firmaCampo}>
            <span className={styles.label}>Celular</span>
            <span className={styles.valor} />
          </div>
        </div>
      </div>
    </div>
  );
}
