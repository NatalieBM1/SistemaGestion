import { CatalogoCRUD } from "../../components/CatalogoCRUD";
import { CATALOGOS } from "../../config/catalogos";

export function PrefijosFacturaPage() {
  return <CatalogoCRUD config={CATALOGOS.prefijos_factura} />;
}
