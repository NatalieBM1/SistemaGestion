import { CatalogoCRUD } from "../../components/CatalogoCRUD";
import { CATALOGOS } from "../../config/catalogos";

export function FormasPagoPage() {
  return <CatalogoCRUD config={CATALOGOS.formas_pago} />;
}
