import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getRemisionesDeFactura } from "../../api/facturas";
import { Badge, Button, EmptyState } from "../../components/ui";
import { formatMoney } from "../../lib/format";
import { usePageTitle } from "../../store/pageTitleStore";
import tableStyles from "../../components/ui/Table.module.css";

export function DetalleFactura() {
  const params = useParams<{ numeroFactura: string }>();
  const numeroFactura = decodeURIComponent(params.numeroFactura ?? "");
  const navigate = useNavigate();

  usePageTitle(`Factura ${numeroFactura}`);

  const { data: remisiones, isLoading } = useQuery({
    queryKey: ["factura-remisiones", numeroFactura],
    queryFn: () => getRemisionesDeFactura(numeroFactura),
    enabled: Boolean(numeroFactura),
  });

  const valorTotal = (remisiones ?? [])
    .filter((r) => !r.anulada)
    .reduce((sum, r) => sum + Number(r.valor_facturado), 0);

  return (
    <div>
      <Button variant="ghost" leftIcon={<ArrowLeft size={16} />} onClick={() => navigate("/facturas")}>
        Volver a facturas
      </Button>

      <div style={{ margin: "var(--space-4) 0" }}>
        <h2 style={{ margin: 0 }} className="font-mono-data">
          {numeroFactura}
        </h2>
        <p style={{ color: "var(--text-secondary)", margin: "var(--space-1) 0 0" }}>
          Valor total facturado (activas): <strong>{formatMoney(valorTotal)}</strong>
        </p>
      </div>

      {!isLoading && (remisiones ?? []).length === 0 ? (
        <EmptyState title="Sin remisiones" description="Esta factura no tiene remisiones asociadas." />
      ) : (
        <div className={tableStyles.wrapper}>
          <table className={tableStyles.table}>
            <thead>
              <tr>
                <th>Remisión</th>
                <th>Tipo</th>
                <th>Valor facturado</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {(remisiones ?? []).map((r) => (
                <tr key={r.id} style={{ opacity: r.anulada ? 0.55 : 1 }}>
                  <td>
                    <Link to={`/remisiones/${r.remision_id}`} style={{ color: "var(--accent)", fontWeight: 500 }} className="font-mono-data">
                      {r.numero_remision ?? r.remision_id}
                    </Link>
                  </td>
                  <td>{r.tipo_facturacion}</td>
                  <td className="font-mono-data">{formatMoney(r.valor_facturado)}</td>
                  <td>
                    <Badge variant={r.anulada ? "danger" : "success"}>{r.anulada ? "Anulada" : "Activa"}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
