import { CatalogoCRUD } from "../../components/CatalogoCRUD";
import { CATALOGOS } from "../../config/catalogos";

export function UnidadesMedidaPage() {
  return <CatalogoCRUD config={CATALOGOS.unidades_medida} />;
}
