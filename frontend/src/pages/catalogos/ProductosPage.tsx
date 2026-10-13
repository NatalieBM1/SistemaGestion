import { CatalogoCRUD } from "../../components/CatalogoCRUD";
import { CATALOGOS } from "../../config/catalogos";

export function ProductosPage() {
  return <CatalogoCRUD config={CATALOGOS.productos} />;
}
