import { CatalogoCRUD } from "../../components/CatalogoCRUD";
import { CATALOGOS } from "../../config/catalogos";

export function TiposTerceroPage() {
  return <CatalogoCRUD config={CATALOGOS.tipos_tercero} />;
}
